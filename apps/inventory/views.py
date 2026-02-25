from datetime import date
from decimal import Decimal, InvalidOperation
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from twilio.rest import Client

from apps.core.permissions import can_read_inventory, can_write_inventory
from apps.core.utils import get_evento_atual

from .forms import (
    CotacaoCompraForm,
    CotacaoCompraItemFormSet,
    CotacaoAprovacaoForm,
    EntradaEstoqueForm,
    FornecedorForm,
    ProdutoForm,
    RequisicaoSaidaForm,
    RequisicaoSaidaItemFormSet,
)
from .models import (
    EntradaEstoque,
    CotacaoCompra,
    CotacaoCompraImpressao,
    CotacaoCompraPreco,
    Fornecedor,
    OrdemCompra,
    Produto,
    RequisicaoSaida,
    RequisicaoSaidaImpressao,
)
from apps.finance.models import LancamentoFinanceiro


TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")


def _validar_itens_formset(formset, mensagem_vazio):
    itens_validos = [
        f
        for f in formset.forms
        if f.cleaned_data
        and not f.cleaned_data.get("DELETE", False)
        and f.cleaned_data.get("produto")
        and f.cleaned_data.get("quantidade")
    ]
    if not itens_validos:
        raise ValidationError(mensagem_vazio)

    produtos_ids = [f.cleaned_data["produto"].pk for f in itens_validos]
    if len(produtos_ids) != len(set(produtos_ids)):
        raise ValidationError("Nao repita o mesmo produto em multiplas linhas.")

    return itens_validos


def _coletar_precos_cotacao(request, itens_forms, fornecedores):
    dados = []
    for item_form in itens_forms:
        produto = item_form.cleaned_data["produto"]
        precos_fornecedor = {}

        for fornecedor in fornecedores:
            campo = f"preco_{item_form.prefix}_{fornecedor.id}"
            valor_txt = (request.POST.get(campo) or "").strip()
            if not valor_txt:
                continue
            try:
                valor = Decimal(valor_txt)
            except InvalidOperation as exc:
                raise ValidationError(f"Valor invalido para {fornecedor.nome} no item {produto.nome}.") from exc
            if valor < 0:
                raise ValidationError(f"Valor negativo para {fornecedor.nome} no item {produto.nome}.")
            precos_fornecedor[fornecedor.id] = valor

        if not precos_fornecedor:
            raise ValidationError(f"Informe ao menos um preco para o item {produto.nome}.")

        dados.append(
            {
                "produto_id": produto.id,
                "precos": precos_fornecedor,
            }
        )

    return dados


def _salvar_precos_cotacao(cotacao, dados_precos):
    CotacaoCompraPreco.objects.filter(cotacao=cotacao).delete()

    itens_por_produto = {item.produto_id: item for item in cotacao.itens.all()}
    fornecedores = {f.id: f for f in Fornecedor.objects.filter(ativo=True)}

    objetos = []
    for dado in dados_precos:
        item = itens_por_produto[dado["produto_id"]]
        for fornecedor_id, valor_unitario in dado["precos"].items():
            fornecedor = fornecedores.get(fornecedor_id)
            if not fornecedor:
                continue
            objetos.append(
                CotacaoCompraPreco(
                    cotacao=cotacao,
                    item=item,
                    fornecedor=fornecedor,
                    valor_unitario=valor_unitario,
                    valor_total=item.quantidade * valor_unitario,
                )
            )

    if objetos:
        CotacaoCompraPreco.objects.bulk_create(objetos)


def _montar_mensagem_ordem_compra(ordem, cotacao, fornecedor, mapa_precos):
    linhas = []
    total = Decimal("0.00")
    for item in cotacao.itens.select_related("produto").all():
        preco = mapa_precos.get(item.id)
        if not preco:
            continue
        subtotal = item.quantidade * preco.valor_unitario
        total += subtotal
        linhas.append(
            f"- {item.produto.nome}: {item.quantidade} x R$ {preco.valor_unitario} = R$ {subtotal}"
        )
    corpo = "\n".join(linhas)
    return (
        f"*Ordem de Compra {ordem.numero}*\n"
        f"Cotacao: {cotacao.numero}\n"
        f"Fornecedor: {fornecedor.nome}\n\n"
        f"Itens:\n{corpo}\n\n"
        f"Total: R$ {total}\n"
        "Favor confirmar recebimento."
    )


def _enviar_ordem_compra_whatsapp(ordem_id, telefone):
    ordem = OrdemCompra.objects.select_related("cotacao", "fornecedor").get(pk=ordem_id)
    if not telefone:
        ordem.status_envio = OrdemCompra.FALHA
        ordem.erro_envio = "Fornecedor sem telefone para WhatsApp."
        ordem.save(update_fields=["status_envio", "erro_envio"])
        return

    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        ordem.status_envio = OrdemCompra.FALHA
        ordem.erro_envio = "Credenciais Twilio nao configuradas."
        ordem.save(update_fields=["status_envio", "erro_envio"])
        return

    numero_destino = telefone.strip()
    if not numero_destino.startswith("whatsapp:"):
        numero_destino = f"whatsapp:{numero_destino}"

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=numero_destino,
            body=ordem.mensagem,
        )
        ordem.status_envio = OrdemCompra.ENVIADA
        ordem.twilio_sid = message.sid
        ordem.enviada_em = timezone.now()
        ordem.erro_envio = ""
        ordem.save(update_fields=["status_envio", "twilio_sid", "enviada_em", "erro_envio"])
    except Exception as exc:
        ordem.status_envio = OrdemCompra.FALHA
        ordem.erro_envio = str(exc)[:255]
        ordem.save(update_fields=["status_envio", "erro_envio"])


def _montar_linhas_cotacao(formset, fornecedores, post_data=None, existentes=None):
    linhas = []
    existentes = existentes or {}
    for item_form in formset.forms:
        item_id = item_form.instance.pk
        precos = []
        for fornecedor in fornecedores:
            field_name = f"preco_{item_form.prefix}_{fornecedor.id}"
            if post_data is not None:
                valor = post_data.get(field_name, "")
            else:
                valor = str(existentes.get(f"{item_id}:{fornecedor.id}", "")) if item_id else ""
            precos.append(
                {
                    "fornecedor": fornecedor,
                    "field_name": field_name,
                    "value": valor,
                }
            )
        linhas.append({"form": item_form, "precos": precos})
    return linhas


@login_required
@user_passes_test(can_read_inventory)
def dashboard(request):
    evento = get_evento_atual(request)
    produtos = Produto.objects.all()
    requisicoes_evento = RequisicaoSaida.objects.filter(evento=evento) if evento else RequisicaoSaida.objects.none()
    cotacoes_evento = CotacaoCompra.objects.filter(evento=evento) if evento else CotacaoCompra.objects.none()

    total_estoque = produtos.aggregate(total=Sum("estoque_atual"))["total"] or 0
    contexto = {
        "evento": evento,
        "produtos_total": produtos.count(),
        "alerta_baixo": produtos.filter(estoque_atual__lt=F("estoque_minimo")).count(),
        "alerta_reabastecimento": produtos.filter(
            estoque_reabastecimento__gt=0, estoque_atual__lt=F("estoque_reabastecimento")
        ).count(),
        "alerta_acima": produtos.filter(estoque_maximo__gt=0, estoque_atual__gt=F("estoque_maximo")).count(),
        "total_estoque": total_estoque,
        "requisicoes_abertas": requisicoes_evento.filter(status=RequisicaoSaida.ABERTA).count(),
        "requisicoes_finalizadas": requisicoes_evento.filter(status=RequisicaoSaida.FINALIZADA).count(),
        "cotacoes_abertas": cotacoes_evento.filter(status=CotacaoCompra.ABERTA).count(),
        "pode_editar": can_write_inventory(request.user),
    }
    return render(request, "inventory/dashboard.html", contexto)


@login_required
@user_passes_test(can_read_inventory)
def produtos_lista(request):
    queryset = Produto.objects.order_by("nome")
    status = request.GET.get("status")
    busca = request.GET.get("busca")
    categoria = request.GET.get("categoria")

    if busca:
        queryset = queryset.filter(nome__icontains=busca)
    if categoria:
        queryset = queryset.filter(categoria=categoria)
    if status == "baixo":
        queryset = [p for p in queryset if p.status_estoque == "BAIXO"]
    elif status == "reabastecer":
        queryset = [p for p in queryset if p.status_estoque == "REABASTECER"]
    elif status == "acima":
        queryset = [p for p in queryset if p.status_estoque == "ACIMA"]

    if not isinstance(queryset, list):
        queryset = list(queryset)

    paginator = Paginator(queryset, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    totais = {
        "total": len(queryset),
        "baixo": len([p for p in queryset if p.status_estoque == "BAIXO"]),
        "reabastecer": len([p for p in queryset if p.status_estoque == "REABASTECER"]),
        "acima": len([p for p in queryset if p.status_estoque == "ACIMA"]),
    }

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    return render(
        request,
        "inventory/produtos_lista.html",
        {
            "page_obj": page_obj,
            "totais": totais,
            "filtros": {"status": status or "", "busca": busca or "", "categoria": categoria or ""},
            "categorias": Produto.CATEGORIA_CHOICES,
            "querystring": query_params.urlencode(),
            "pode_editar": can_write_inventory(request.user),
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def produto_criar(request):
    if request.method == "POST":
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto cadastrado com sucesso.")
            return redirect(reverse("inventory:produtos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = ProdutoForm()

    return render(request, "inventory/produto_form.html", {"form": form, "acao": "Novo"})


@login_required
@user_passes_test(can_write_inventory)
def entrada_criar(request):
    if request.method == "POST":
        form = EntradaEstoqueForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                entrada = form.save(commit=False)
                entrada.criado_por = request.user

                produto = Produto.objects.select_for_update().get(pk=entrada.produto_id)
                produto.registrar_entrada(entrada.quantidade, entrada.custo_unitario)
                produto.save(update_fields=["estoque_atual", "valor_estoque_atual", "custo_medio_atual"])

                entrada.save()
            messages.success(request, "Entrada registrada com sucesso.")
            return redirect(reverse("inventory:produtos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = EntradaEstoqueForm(initial={"data": date.today()})

    return render(request, "inventory/entrada_form.html", {"form": form})


@login_required
@user_passes_test(can_read_inventory)
def movimentos_lista(request):
    evento = get_evento_atual(request)
    queryset = (
        RequisicaoSaida.objects.filter(evento=evento)
        .select_related("evento", "criado_por", "finalizado_por")
        .prefetch_related("itens__produto")
        if evento
        else RequisicaoSaida.objects.none()
    )

    status = request.GET.get("status")
    area = request.GET.get("area")

    if status:
        queryset = queryset.filter(status=status)
    if area:
        queryset = queryset.filter(area=area)

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    return render(
        request,
        "inventory/requisicoes_lista.html",
        {
            "page_obj": page_obj,
            "evento": evento,
            "filtros": {"status": status or "", "area": area or ""},
            "querystring": query_params.urlencode(),
            "status_choices": RequisicaoSaida.STATUS_CHOICES,
            "area_choices": RequisicaoSaida.AREAS_CHOICES,
            "pode_editar": can_write_inventory(request.user),
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def movimentacao_criar(request):
    return redirect(reverse("inventory:requisicao_criar"))


@login_required
@user_passes_test(can_write_inventory)
def requisicao_criar(request):
    evento = get_evento_atual(request)
    if not evento:
        messages.error(request, "Selecione um evento antes de criar requisicoes.")
        return redirect(reverse("core:selecionar_evento"))

    if request.method == "POST":
        form = RequisicaoSaidaForm(request.POST)
        formset = RequisicaoSaidaItemFormSet(request.POST, prefix="itens")

        if form.is_valid() and formset.is_valid():
            try:
                _validar_itens_formset(formset, "Adicione ao menos um item na requisicao.")
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                with transaction.atomic():
                    requisicao = form.save(commit=False)
                    requisicao.evento = evento
                    requisicao.criado_por = request.user
                    requisicao.save()

                    formset.instance = requisicao
                    formset.save()

                messages.success(request, f"Requisicao {requisicao.numero} criada com sucesso.")
                return redirect(reverse("inventory:movimentos_lista"))
        else:
            messages.error(request, "Corrija os erros do formulario.")
    else:
        form = RequisicaoSaidaForm()
        formset = RequisicaoSaidaItemFormSet(prefix="itens")

    return render(
        request,
        "inventory/requisicao_form.html",
        {
            "form": form,
            "formset": formset,
            "evento": evento,
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def requisicao_editar(request, pk):
    evento = get_evento_atual(request)
    requisicao = get_object_or_404(RequisicaoSaida, pk=pk, evento=evento)
    if requisicao.status != RequisicaoSaida.ABERTA:
        messages.error(request, "Somente requisicoes abertas podem ser editadas.")
        return redirect(reverse("inventory:movimentos_lista"))

    if request.method == "POST":
        form = RequisicaoSaidaForm(request.POST, instance=requisicao)
        formset = RequisicaoSaidaItemFormSet(request.POST, instance=requisicao, prefix="itens")

        if form.is_valid() and formset.is_valid():
            try:
                _validar_itens_formset(formset, "Adicione ao menos um item na requisicao.")
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                with transaction.atomic():
                    form.save()
                    formset.save()
                messages.success(request, f"Requisicao {requisicao.numero} atualizada com sucesso.")
                return redirect(reverse("inventory:movimentos_lista"))
        else:
            messages.error(request, "Corrija os erros do formulario.")
    else:
        form = RequisicaoSaidaForm(instance=requisicao)
        formset = RequisicaoSaidaItemFormSet(instance=requisicao, prefix="itens")

    return render(
        request,
        "inventory/requisicao_form.html",
        {
            "form": form,
            "formset": formset,
            "evento": evento,
            "requisicao": requisicao,
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def requisicao_finalizar(request, pk):
    if request.method != "POST":
        return redirect(reverse("inventory:movimentos_lista"))

    evento = get_evento_atual(request)
    requisicao = get_object_or_404(RequisicaoSaida, pk=pk, evento=evento)

    try:
        requisicao.finalizar(request.user)
    except ValidationError as exc:
        if hasattr(exc, "messages"):
            for msg in exc.messages:
                messages.error(request, msg)
        else:
            messages.error(request, "Nao foi possivel finalizar a requisicao.")
    else:
        messages.success(request, f"Requisicao {requisicao.numero} finalizada com sucesso.")

    return redirect(reverse("inventory:movimentos_lista"))


@login_required
@user_passes_test(can_write_inventory)
def requisicao_cancelar(request, pk):
    if request.method != "POST":
        return redirect(reverse("inventory:movimentos_lista"))

    evento = get_evento_atual(request)
    requisicao = get_object_or_404(RequisicaoSaida, pk=pk, evento=evento)
    if requisicao.status != RequisicaoSaida.ABERTA:
        messages.error(request, "Somente requisicoes abertas podem ser canceladas.")
        return redirect(reverse("inventory:movimentos_lista"))

    requisicao.status = RequisicaoSaida.CANCELADA
    requisicao.save(update_fields=["status"])
    messages.success(request, f"Requisicao {requisicao.numero} cancelada.")
    return redirect(reverse("inventory:movimentos_lista"))


@login_required
@user_passes_test(can_read_inventory)
def requisicao_comprovante(request, pk):
    evento = get_evento_atual(request)
    requisicao = get_object_or_404(
        RequisicaoSaida.objects.select_related("evento", "criado_por", "finalizado_por").prefetch_related("itens__produto"),
        pk=pk,
        evento=evento,
    )

    via = request.GET.get("via", RequisicaoSaidaImpressao.ORIGINAL)
    if via not in {RequisicaoSaidaImpressao.ORIGINAL, RequisicaoSaidaImpressao.SEGUNDA_VIA}:
        via = RequisicaoSaidaImpressao.ORIGINAL

    with transaction.atomic():
        RequisicaoSaidaImpressao.objects.create(
            requisicao=requisicao,
            impresso_por=request.user,
            via=via,
        )
        requisicao.impresso_em = timezone.now()
        requisicao.impresso_por = request.user
        requisicao.save(update_fields=["impresso_em", "impresso_por"])

    return render(
        request,
        "inventory/requisicao_comprovante.html",
        {
            "requisicao": requisicao,
            "via": via,
        },
    )


@login_required
@user_passes_test(can_read_inventory)
def fornecedores_lista(request):
    fornecedores = Fornecedor.objects.order_by("nome")
    busca = request.GET.get("busca")
    if busca:
        fornecedores = fornecedores.filter(nome__icontains=busca)

    return render(
        request,
        "inventory/fornecedores_lista.html",
        {
            "fornecedores": fornecedores,
            "busca": busca or "",
            "pode_editar": can_write_inventory(request.user),
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def fornecedor_criar(request):
    if request.method == "POST":
        form = FornecedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fornecedor cadastrado com sucesso.")
            return redirect(reverse("inventory:fornecedores_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = FornecedorForm()

    return render(request, "inventory/fornecedor_form.html", {"form": form, "acao": "Novo"})


@login_required
@user_passes_test(can_read_inventory)
def cotacoes_lista(request):
    evento = get_evento_atual(request)
    queryset = (
        CotacaoCompra.objects.filter(evento=evento)
        .select_related("evento", "criado_por", "fechado_por")
        .prefetch_related("itens__produto", "precos__fornecedor")
        if evento
        else CotacaoCompra.objects.none()
    )

    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    return render(
        request,
        "inventory/cotacoes_lista.html",
        {
            "evento": evento,
            "page_obj": page_obj,
            "status_choices": CotacaoCompra.STATUS_CHOICES,
            "filtros": {"status": status or ""},
            "querystring": query_params.urlencode(),
            "pode_editar": can_write_inventory(request.user),
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def cotacao_criar(request):
    evento = get_evento_atual(request)
    if not evento:
        messages.error(request, "Selecione um evento antes de criar cotacoes.")
        return redirect(reverse("core:selecionar_evento"))

    fornecedores = list(Fornecedor.objects.filter(ativo=True).order_by("nome"))
    if not fornecedores:
        messages.error(request, "Cadastre ao menos um fornecedor ativo antes de criar cotacoes.")
        return redirect(reverse("inventory:fornecedor_criar"))

    if request.method == "POST":
        form = CotacaoCompraForm(request.POST)
        formset = CotacaoCompraItemFormSet(request.POST, prefix="itens")

        if form.is_valid() and formset.is_valid():
            try:
                itens_validos = _validar_itens_formset(formset, "Adicione ao menos um item na cotacao.")
                dados_precos = _coletar_precos_cotacao(request, itens_validos, fornecedores)
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                with transaction.atomic():
                    cotacao = form.save(commit=False)
                    cotacao.evento = evento
                    cotacao.criado_por = request.user
                    cotacao.save()

                    formset.instance = cotacao
                    formset.save()

                    _salvar_precos_cotacao(cotacao, dados_precos)

                messages.success(request, f"Cotacao {cotacao.numero} criada com sucesso.")
                return redirect(reverse("inventory:cotacoes_lista"))
        else:
            messages.error(request, "Corrija os erros do formulario.")
    else:
        form = CotacaoCompraForm()
        formset = CotacaoCompraItemFormSet(prefix="itens")

    linhas_cotacao = _montar_linhas_cotacao(
        formset,
        fornecedores,
        post_data=request.POST if request.method == "POST" else None,
    )

    return render(
        request,
        "inventory/cotacao_form.html",
        {
            "evento": evento,
            "form": form,
            "formset": formset,
            "fornecedores": fornecedores,
            "linhas_cotacao": linhas_cotacao,
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def cotacao_editar(request, pk):
    evento = get_evento_atual(request)
    cotacao = get_object_or_404(CotacaoCompra, pk=pk, evento=evento)
    if cotacao.status != CotacaoCompra.ABERTA:
        messages.error(request, "Somente cotacoes em aberto podem ser editadas.")
        return redirect(reverse("inventory:cotacoes_lista"))

    fornecedores = list(Fornecedor.objects.filter(ativo=True).order_by("nome"))

    if request.method == "POST":
        form = CotacaoCompraForm(request.POST, instance=cotacao)
        formset = CotacaoCompraItemFormSet(request.POST, instance=cotacao, prefix="itens")

        if form.is_valid() and formset.is_valid():
            try:
                itens_validos = _validar_itens_formset(formset, "Adicione ao menos um item na cotacao.")
                dados_precos = _coletar_precos_cotacao(request, itens_validos, fornecedores)
            except ValidationError as exc:
                for msg in exc.messages:
                    messages.error(request, msg)
            else:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    _salvar_precos_cotacao(cotacao, dados_precos)
                messages.success(request, f"Cotacao {cotacao.numero} atualizada com sucesso.")
                return redirect(reverse("inventory:cotacoes_lista"))
        else:
            messages.error(request, "Corrija os erros do formulario.")
    else:
        form = CotacaoCompraForm(instance=cotacao)
        formset = CotacaoCompraItemFormSet(instance=cotacao, prefix="itens")

    precos_existentes = {
        f"{preco.item_id}:{preco.fornecedor_id}": preco.valor_unitario
        for preco in cotacao.precos.select_related("fornecedor")
    }
    linhas_cotacao = _montar_linhas_cotacao(
        formset,
        fornecedores,
        post_data=request.POST if request.method == "POST" else None,
        existentes=precos_existentes,
    )

    return render(
        request,
        "inventory/cotacao_form.html",
        {
            "evento": evento,
            "form": form,
            "formset": formset,
            "fornecedores": fornecedores,
            "cotacao": cotacao,
            "linhas_cotacao": linhas_cotacao,
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def cotacao_fechar(request, pk):
    if request.method != "POST":
        return redirect(reverse("inventory:cotacoes_lista"))

    evento = get_evento_atual(request)
    cotacao = get_object_or_404(CotacaoCompra, pk=pk, evento=evento)
    try:
        cotacao.fechar(request.user)
    except ValidationError as exc:
        for msg in exc.messages:
            messages.error(request, msg)
    else:
        messages.success(request, f"Cotacao {cotacao.numero} fechada com sucesso.")

    return redirect(reverse("inventory:cotacoes_lista"))


@login_required
@user_passes_test(can_write_inventory)
def cotacao_cancelar(request, pk):
    if request.method != "POST":
        return redirect(reverse("inventory:cotacoes_lista"))

    evento = get_evento_atual(request)
    cotacao = get_object_or_404(CotacaoCompra, pk=pk, evento=evento)
    if cotacao.status != CotacaoCompra.ABERTA:
        messages.error(request, "Somente cotacoes em aberto podem ser canceladas.")
        return redirect(reverse("inventory:cotacoes_lista"))

    cotacao.status = CotacaoCompra.CANCELADA
    cotacao.save(update_fields=["status"])
    messages.success(request, f"Cotacao {cotacao.numero} cancelada.")
    return redirect(reverse("inventory:cotacoes_lista"))


@login_required
@user_passes_test(can_read_inventory)
def cotacao_comprovante(request, pk):
    evento = get_evento_atual(request)
    cotacao = get_object_or_404(
        CotacaoCompra.objects.select_related("evento", "criado_por", "fechado_por").prefetch_related(
            "itens__produto", "precos__fornecedor", "precos__item"
        ),
        pk=pk,
        evento=evento,
    )

    via = request.GET.get("via", CotacaoCompraImpressao.ORIGINAL)
    if via not in {CotacaoCompraImpressao.ORIGINAL, CotacaoCompraImpressao.SEGUNDA_VIA}:
        via = CotacaoCompraImpressao.ORIGINAL

    with transaction.atomic():
        CotacaoCompraImpressao.objects.create(cotacao=cotacao, impresso_por=request.user, via=via)

    totais = cotacao.totais_por_fornecedor()
    return render(
        request,
        "inventory/cotacao_comprovante.html",
        {
            "cotacao": cotacao,
            "via": via,
            "fornecedores": sorted([registro["fornecedor"] for registro in totais.values()], key=lambda x: x.nome),
            "totais": totais,
        },
    )


@login_required
@user_passes_test(can_write_inventory)
def cotacao_aprovar(request, pk):
    evento = get_evento_atual(request)
    cotacao = get_object_or_404(
        CotacaoCompra.objects.select_related("evento").prefetch_related("itens__produto"),
        pk=pk,
        evento=evento,
    )
    if cotacao.status != CotacaoCompra.ABERTA:
        messages.error(request, "Somente cotacoes em aberto podem ser aprovadas.")
        return redirect(reverse("inventory:cotacoes_lista"))

    fornecedor_ids = cotacao.precos.values_list("fornecedor_id", flat=True).distinct()
    fornecedores = Fornecedor.objects.filter(id__in=fornecedor_ids, ativo=True).order_by("nome")
    if not fornecedores.exists():
        messages.error(request, "A cotacao nao possui fornecedores ativos com preco informado.")
        return redirect(reverse("inventory:cotacoes_lista"))

    if request.method == "POST":
        form = CotacaoAprovacaoForm(request.POST, fornecedores=fornecedores)
        if form.is_valid():
            fornecedor = form.cleaned_data["fornecedor"]
            precos_fornecedor = {
                preco.item_id: preco
                for preco in CotacaoCompraPreco.objects.select_related("item")
                .filter(cotacao=cotacao, fornecedor=fornecedor)
            }

            itens = list(cotacao.itens.all())
            faltantes = [item.produto.nome for item in itens if item.id not in precos_fornecedor]
            if faltantes:
                messages.error(
                    request,
                    "Fornecedor sem preco para os itens: " + ", ".join(faltantes),
                )
            else:
                total_aprovado = sum(
                    [item.quantidade * precos_fornecedor[item.id].valor_unitario for item in itens],
                    start=Decimal("0.00"),
                )

                with transaction.atomic():
                    cotacao_locked = CotacaoCompra.objects.select_for_update().get(pk=cotacao.pk)
                    if hasattr(cotacao_locked, "ordem_compra"):
                        messages.error(request, "Esta cotacao ja possui ordem de compra.")
                        return redirect(reverse("inventory:cotacoes_lista"))

                    lancamento = LancamentoFinanceiro.objects.create(
                        evento=cotacao_locked.evento,
                        tipo=LancamentoFinanceiro.DESPESA,
                        categoria=form.cleaned_data["categoria_despesa"],
                        conta=form.cleaned_data["conta"],
                        data=form.cleaned_data["data"],
                        descricao=f"OC {cotacao_locked.numero} - {fornecedor.nome}",
                        valor=total_aprovado,
                        forma_pagamento=form.cleaned_data["forma_pagamento"],
                        criado_por=request.user,
                        atualizado_por=request.user,
                    )

                    ordem = OrdemCompra.objects.create(
                        cotacao=cotacao_locked,
                        fornecedor=fornecedor,
                        mensagem="",
                        valor_total=total_aprovado,
                        criado_por=request.user,
                    )

                    for item in itens:
                        preco = precos_fornecedor[item.id]
                        produto = Produto.objects.select_for_update().get(pk=item.produto_id)
                        produto.registrar_entrada(item.quantidade, preco.valor_unitario)
                        produto.save(update_fields=["estoque_atual", "valor_estoque_atual", "custo_medio_atual"])

                        EntradaEstoque.objects.create(
                            produto=produto,
                            data=form.cleaned_data["data"],
                            quantidade=item.quantidade,
                            custo_unitario=preco.valor_unitario,
                            documento=ordem.numero,
                            observacao=f"Entrada automatica por aprovacao da {cotacao_locked.numero}",
                            criado_por=request.user,
                        )

                    ordem.mensagem = _montar_mensagem_ordem_compra(
                        ordem, cotacao_locked, fornecedor, precos_fornecedor
                    )
                    ordem.save(update_fields=["mensagem"])

                    cotacao_locked.status = CotacaoCompra.FECHADA
                    cotacao_locked.fechado_em = timezone.now()
                    cotacao_locked.fechado_por = request.user
                    cotacao_locked.fornecedor_aprovado = fornecedor
                    cotacao_locked.valor_aprovado = total_aprovado
                    cotacao_locked.aprovado_em = timezone.now()
                    cotacao_locked.aprovado_por = request.user
                    cotacao_locked.lancamento_financeiro = lancamento
                    cotacao_locked.save(
                        update_fields=[
                            "status",
                            "fechado_em",
                            "fechado_por",
                            "fornecedor_aprovado",
                            "valor_aprovado",
                            "aprovado_em",
                            "aprovado_por",
                            "lancamento_financeiro",
                        ]
                    )

                    telefone = fornecedor.telefone
                    transaction.on_commit(lambda: _enviar_ordem_compra_whatsapp(ordem.id, telefone))

                messages.success(
                    request,
                    (
                        f"Cotacao {cotacao.numero} aprovada. "
                        f"OC {ordem.numero} criada, estoque atualizado e despesa lancada."
                    ),
                )
                return redirect(reverse("inventory:cotacoes_lista"))
        else:
            messages.error(request, "Corrija os erros do formulario de aprovacao.")
    else:
        form = CotacaoAprovacaoForm(
            fornecedores=fornecedores,
            initial={
                "fornecedor": fornecedores.first(),
                "data": date.today(),
                "forma_pagamento": LancamentoFinanceiro.PIX,
            },
        )

    totais = cotacao.totais_por_fornecedor()
    return render(
        request,
        "inventory/cotacao_aprovar_form.html",
        {
            "cotacao": cotacao,
            "form": form,
            "totais": sorted(totais.values(), key=lambda x: x["fornecedor"].nome),
        },
    )
