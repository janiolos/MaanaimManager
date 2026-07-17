import json
import logging
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.models import AuditLog
from apps.core.utils import get_evento_atual
from apps.finance.forms import LancamentoFinanceiroForm, AnexoLancamentoForm
from apps.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro, AnexoLancamento
from apps.finance.permissions import can_read_finance, can_write_finance

logger = logging.getLogger(__name__)

def _registrar_auditoria_exclusao_lancamento(request, lancamento, status_code, resultado, motivo=""):
    try:
        detalhes = {
            "acao": "excluir_lancamento",
            "resultado": resultado,
            "motivo": motivo,
            "lancamento": {
                "id": lancamento.id,
                "evento_id": lancamento.evento_id,
                "tipo": lancamento.tipo,
                "data": str(lancamento.data),
                "valor": str(lancamento.valor),
                "descricao": lancamento.descricao,
                "categoria_id": lancamento.categoria_id,
                "conta_id": lancamento.conta_id,
            },
        }
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            method="DELETE",
            path=f"{request.path}?audit={json.dumps(detalhes, ensure_ascii=True, separators=(',', ':'))}",
            view_name="finance:lancamento_excluir",
            status_code=status_code,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
    except Exception:
        logger.exception("Falha ao registrar auditoria de exclusao de lancamento. lancamento_id=%s", getattr(lancamento, "id", None))


@login_required
@user_passes_test(can_read_finance)
def lancamentos_lista(request):
    evento = get_evento_atual(request)
    queryset = LancamentoFinanceiro.objects.all().select_related("categoria", "conta").order_by("-data", "-id")
    if evento: queryset = queryset.filter(evento=evento)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    tipo = request.GET.get("tipo")
    categoria = request.GET.get("categoria")
    conta = request.GET.get("conta")
    texto = request.GET.get("texto")

    if data_inicio: queryset = queryset.filter(data__gte=data_inicio)
    if data_fim: queryset = queryset.filter(data__lte=data_fim)
    if tipo: queryset = queryset.filter(tipo=tipo)
    if categoria: queryset = queryset.filter(categoria_id=categoria)
    if conta: queryset = queryset.filter(conta_id=conta)
    if texto: queryset = queryset.filter(descricao__icontains=texto)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    query_params = request.GET.copy()
    if "page" in query_params: query_params.pop("page")

    context = {
        "page_obj": page_obj,
        "categorias": CategoriaFinanceira.objects.all(),
        "contas": ContaCaixa.objects.all(),
        "formas_pagamento": LancamentoFinanceiro.FORMAS_PAGAMENTO,
        "pode_anexos": can_write_finance(request.user),
        "querystring": query_params.urlencode(),
        "filtros": {
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or "",
            "tipo": tipo or "",
            "categoria": categoria or "",
            "conta": conta or "",
            "texto": texto or "",
        },
    }
    return render(request, "finance/lancamentos_lista.html", context)


@login_required
@user_passes_test(can_read_finance)
def categorias_por_tipo(request):
    tipo = request.GET.get("tipo")
    categorias = CategoriaFinanceira.objects.all()
    if tipo: categorias = categorias.filter(tipo=tipo)
    data = [{"id": c.id, "nome": c.nome, "tipo": c.tipo} for c in categorias]
    return JsonResponse({"categorias": data})


@login_required
@user_passes_test(can_write_finance)
def lancamento_criar(request):
    evento = get_evento_atual(request)
    return_url = request.GET.get("next")
    if request.method == "POST":
        form = LancamentoFinanceiroForm(request.POST)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.evento = evento
            lancamento.criado_por = request.user
            lancamento.atualizado_por = request.user
            lancamento.save()
            messages.success(request, "Lancamento criado com sucesso.")
            next_url = request.GET.get("next") or return_url
            return redirect(next_url or reverse("finance:lancamentos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = LancamentoFinanceiroForm(initial={"data": date.today()})

    categorias = CategoriaFinanceira.objects.all()
    return render(request, "finance/lancamento_form.html", {
            "form": form,
            "acao": "Novo",
            "categorias": categorias,
            "return_url": return_url,
    })


@login_required
@user_passes_test(can_write_finance)
def lancamento_editar(request, lancamento_id):
    evento = get_evento_atual(request)
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id, evento=evento)
    return_url = request.GET.get("next")
    
    if request.method == "POST":
        form = LancamentoFinanceiroForm(request.POST, instance=lancamento)
        if form.is_valid():
            lancamento = form.save(commit=False)
            lancamento.atualizado_por = request.user
            lancamento.save()
            messages.success(request, "Lancamento atualizado com sucesso.")
            next_url = request.GET.get("next") or return_url
            return redirect(next_url or reverse("finance:lancamentos_lista"))
        messages.error(request, "Corrija os erros do formulario.")
    else:
        form = LancamentoFinanceiroForm(instance=lancamento)

    categorias = CategoriaFinanceira.objects.all()
    return render(request, "finance/lancamento_form.html", {
            "form": form,
            "acao": "Editar",
            "lancamento": lancamento,
            "categorias": categorias,
            "return_url": return_url,
    })


@login_required
@user_passes_test(can_write_finance)
def lancamento_excluir(request, lancamento_id):
    evento = get_evento_atual(request)
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id, evento=evento)
    return_url = request.GET.get("next") or request.POST.get("next")
    
    if request.method == "POST":
        try:
            lancamento.delete()
            _registrar_auditoria_exclusao_lancamento(request, lancamento, status_code=200, resultado="sucesso")
            messages.success(request, "Lancamento excluido com sucesso.")
        except ProtectedError:
            logger.exception("Falha ao excluir lancamento protegido. lancamento_id=%s", lancamento.id)
            _registrar_auditoria_exclusao_lancamento(request, lancamento, status_code=409, resultado="falha", motivo="protegido_por_relacionamento")
            messages.error(request, "Nao foi possivel excluir este lancamento porque ele esta vinculado a outro registro.")
        except Exception:
            logger.exception("Erro inesperado ao excluir lancamento. lancamento_id=%s", lancamento.id)
            _registrar_auditoria_exclusao_lancamento(request, lancamento, status_code=500, resultado="falha", motivo="erro_inesperado")
            messages.error(request, "Ocorreu um erro inesperado ao excluir o lancamento.")
        
        next_url = request.GET.get("next") or request.POST.get("next") or return_url
        return redirect(next_url or reverse("finance:lancamentos_lista"))
        
    return render(request, "finance/lancamento_confirmar_excluir.html", {"lancamento": lancamento, "return_url": return_url})


@login_required
@user_passes_test(can_write_finance)
def anexos(request, lancamento_id):
    evento = get_evento_atual(request)
    lancamento = get_object_or_404(LancamentoFinanceiro, id=lancamento_id, evento=evento)
    anexos_qs = AnexoLancamento.objects.filter(lancamento=lancamento)
    return_url = request.GET.get("next")

    if request.method == "POST":
        form = AnexoLancamentoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                anexo = form.save(commit=False)
                anexo.lancamento = lancamento
                anexo.enviado_por = request.user
                anexo.save()
                messages.success(request, "Anexo enviado com sucesso.")
                next_url = request.GET.get("next") or return_url
                return redirect(next_url or reverse("finance:anexos", args=[lancamento.id]))
            except OSError:
                logger.exception("Falha ao salvar anexo de lancamento. lancamento_id=%s", lancamento.id)
                messages.error(request, "Nao foi possivel salvar o anexo no servidor. Verifique permissoes da pasta media.")
        else:
            messages.error(request, "Corrija os erros do formulario.")
    else:
        form = AnexoLancamentoForm()

    return render(request, "finance/lancamento_anexos.html", {
            "lancamento": lancamento,
            "anexos": anexos_qs,
            "form": form,
            "return_url": return_url,
    })
