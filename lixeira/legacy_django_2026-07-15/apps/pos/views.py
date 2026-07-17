"""
API REST do PDV Maanaim.

Endpoints:
  GET  /pos/api/dados/?eventoId=X     → dados iniciais (locais, produtos, etc.)
  GET  /pos/api/locais/               → lista locais por evento
  POST /pos/api/locais/               → criar local
  PUT  /pos/api/locais/<id>/          → editar local (módulos/nome)
  DEL  /pos/api/locais/<id>/          → excluir local

  GET  /pos/api/familias/?localId=X   → famílias de um local
  POST /pos/api/familias/             → criar família
  DEL  /pos/api/familias/<id>/        → excluir família

  GET  /pos/api/produtos-local/?localId=X → sub-estoque do local
  POST /pos/api/produtos-local/           → vincular produto ao local
  PUT  /pos/api/produtos-local/<id>/      → editar preço/estoque
  DEL  /pos/api/produtos-local/<id>/      → desvincular

  POST /pos/api/estoque-local/entrada/    → entrada de estoque no local

  GET  /pos/api/vendas/?eventoId=X&localId=Y → histórico de vendas
  POST /pos/api/vendas/                       → registrar venda (finalizar)
  DEL  /pos/api/vendas/<id>/                  → excluir + reverter estoque

  GET  /pos/                          → serve o SPA PDV HTML
"""

import json
import uuid
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_GET, require_POST

from apps.core.models import Evento
from apps.finance.models import LancamentoFinanceiro, CategoriaFinanceira, ContaCaixa
from apps.inventory.models import Produto
from apps.pos.models import (
    LocalVenda, FamiliaVenda, ProdutoLocal, EntradaEstoqueLocal,
    VendaMobile, PagamentoVenda, ItemVendaMobile,
)


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _json_error(msg, status=400):
    return JsonResponse({'error': msg}, status=status)


def _json_ok(data=None, **kwargs):
    payload = {'ok': True}
    if data is not None:
        payload.update(data)
    payload.update(kwargs)
    return JsonResponse(payload)


def _local_to_dict(local):
    return {
        'id': local.id,
        'nome': local.nome,
        'ativo': local.ativo,
        'modulo_dashboard': local.modulo_dashboard,
        'modulo_pdv': local.modulo_pdv,
        'modulo_vendas': local.modulo_vendas,
        'modulo_produtos': local.modulo_produtos,
        'modulo_estoque': local.modulo_estoque,
    }


def _familia_to_dict(f):
    return {'id': f.id, 'nome': f.nome, 'local_id': f.local_id}


def _produto_local_to_dict(pl):
    return {
        'id': pl.id,
        'produto_id': pl.produto_id,
        'local_id': pl.local_id,
        'familia_id': pl.familia_id,
        'familia': pl.familia.nome if pl.familia else '',
        'familia_nome': pl.familia.nome if pl.familia else '',
        'codigo': pl.produto.sku,
        'nome': pl.produto.nome,
        'unidade': pl.produto.unidade,
        'preco_venda': float(pl.preco_venda),
        'estoque_atual': float(pl.estoque_atual),
        'estoque_minimo': float(pl.estoque_minimo),
        'ponto_reabastecimento': float(pl.ponto_reabastecimento),
        'estoque_maximo': float(pl.estoque_maximo),
        'status_estoque': pl.status_estoque,
        'ativo': pl.ativo,
    }


def _venda_to_dict(v):
    itens = [
        {
            'id': i.id,
            'produto_local_id': i.produto_local_id,
            'codigo': i.codigo_produto,
            'nome': i.nome_produto,
            'familia': i.familia_produto,
            'quantidade': i.quantidade,
            'preco_unitario': float(i.preco_unitario),
            'desconto_perc': float(i.desconto_perc),
            'total_item': float(i.total_item),
        }
        for i in v.itens.all()
    ]
    pagamentos = [
        {'tipo': p.tipo, 'valor': float(p.valor)}
        for p in v.pagamentos.all()
    ]
    return {
        'id': v.id,
        'id_referencia': v.id_referencia,
        'evento_id': v.evento_id,
        'local_id': v.local_id,
        'local_nome': v.local.nome if v.local else '',
        'vendedor': v.vendedor.get_full_name() or v.vendedor.username,
        'data_hora': v.data_hora.strftime('%d/%m/%Y %H:%M:%S'),
        'total': float(v.total),
        'itens': itens,
        'pagamentos': pagamentos,
        'qtd_itens': sum(i['quantidade'] for i in itens),
    }


# ---------------------------------------------------------------------------
# VIEW: SPA PDV
# ---------------------------------------------------------------------------

@login_required
def pdv_view(request):
    """Serve o SPA do PDV completo."""
    return render(request, 'pos/pdv.html', {
        'titulo': 'PDV Maanaim',
        'user_nome': request.user.get_full_name() or request.user.username,
    })


# ---------------------------------------------------------------------------
# API: Dados Iniciais
# ---------------------------------------------------------------------------

@require_GET
@login_required
def api_dados_iniciais(request):
    """
    Retorna todos os eventos ativos + locais + famílias + sub-estoques.
    Se eventoId for passado, retorna apenas aquele evento.
    """
    evento_id = request.GET.get('eventoId')

    qs_eventos = Evento.objects.filter(ativo=True).order_by('-data_inicio')
    if evento_id:
        qs_eventos = qs_eventos.filter(pk=evento_id)

    eventos_data = []
    for evento in qs_eventos:
        locais = evento.locais_venda.filter(ativo=True).prefetch_related(
            'familias', 'produtos__produto', 'produtos__familia'
        )
        locais_data = []
        for local in locais:
            familias = [_familia_to_dict(f) for f in local.familias.all()]
            produtos = [_produto_local_to_dict(pl) for pl in local.produtos.filter(ativo=True)]
            locais_data.append({
                **_local_to_dict(local),
                'familias': familias,
                'produtos': produtos,
            })
        eventos_data.append({
            'id': evento.id,
            'nome': str(evento),
            'status': evento.status,
            'locais': locais_data,
        })

    # Catálogo global de produtos (para vincular ao local)
    catalogo = [
        {'id': p.id, 'nome': p.nome, 'sku': p.sku, 'unidade': p.unidade}
        for p in Produto.objects.filter(ativo=True).order_by('nome')
    ]

    return JsonResponse({
        'vendedor': request.user.get_full_name() or request.user.username,
        'eventos': eventos_data,
        'catalogo_produtos': catalogo,
    })


# ---------------------------------------------------------------------------
# API: Locais de Venda
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_locais(request):
    if request.method == 'GET':
        evento_id = request.GET.get('eventoId')
        qs = LocalVenda.objects.all()
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        return JsonResponse({'locais': [_local_to_dict(l) for l in qs]})

    # POST: criar local
    data = json.loads(request.body)
    evento_id = data.get('eventoId')
    nome = (data.get('nome') or '').strip()
    if not evento_id or not nome:
        return _json_error('eventoId e nome são obrigatórios.')
    try:
        evento = Evento.objects.get(pk=evento_id)
    except Evento.DoesNotExist:
        return _json_error('Evento não encontrado.', 404)

    local, created = LocalVenda.objects.get_or_create(
        evento=evento, nome=nome,
        defaults={
            'modulo_dashboard': data.get('modulo_dashboard', True),
            'modulo_pdv': data.get('modulo_pdv', True),
            'modulo_vendas': data.get('modulo_vendas', True),
            'modulo_produtos': data.get('modulo_produtos', False),
            'modulo_estoque': data.get('modulo_estoque', True),
        }
    )
    if not created:
        return _json_error('Já existe um local com este nome neste evento.', 409)
    return JsonResponse({'local': _local_to_dict(local)}, status=201)


@login_required
@require_http_methods(['PUT', 'DELETE'])
def api_local_detail(request, local_id):
    try:
        local = LocalVenda.objects.get(pk=local_id)
    except LocalVenda.DoesNotExist:
        return _json_error('Local não encontrado.', 404)

    if request.method == 'DELETE':
        local.delete()
        return _json_ok()

    # PUT: atualizar
    data = json.loads(request.body)
    for campo in ('nome', 'ativo', 'modulo_dashboard', 'modulo_pdv',
                  'modulo_vendas', 'modulo_produtos', 'modulo_estoque'):
        if campo in data:
            setattr(local, campo, data[campo])
    local.save()
    return JsonResponse({'local': _local_to_dict(local)})


# ---------------------------------------------------------------------------
# API: Famílias
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_familias(request):
    if request.method == 'GET':
        local_id = request.GET.get('localId')
        qs = FamiliaVenda.objects.all()
        if local_id:
            qs = qs.filter(local_id=local_id)
        return JsonResponse({'familias': [_familia_to_dict(f) for f in qs]})

    data = json.loads(request.body)
    local_id = data.get('localId')
    nome = (data.get('nome') or '').strip()
    if not local_id or not nome:
        return _json_error('localId e nome são obrigatórios.')
    try:
        local = LocalVenda.objects.get(pk=local_id)
    except LocalVenda.DoesNotExist:
        return _json_error('Local não encontrado.', 404)

    familia, created = FamiliaVenda.objects.get_or_create(local=local, nome=nome)
    if not created:
        return _json_error('Família já existe neste local.', 409)
    return JsonResponse({'familia': _familia_to_dict(familia)}, status=201)


@login_required
@require_http_methods(['DELETE'])
def api_familia_detail(request, familia_id):
    try:
        FamiliaVenda.objects.get(pk=familia_id).delete()
    except FamiliaVenda.DoesNotExist:
        return _json_error('Família não encontrada.', 404)
    return _json_ok()


# ---------------------------------------------------------------------------
# API: Sub-Estoque (ProdutoLocal)
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_produtos_local(request):
    if request.method == 'GET':
        local_id = request.GET.get('localId')
        qs = ProdutoLocal.objects.select_related('produto', 'familia').all()
        if local_id:
            qs = qs.filter(local_id=local_id)
        return JsonResponse({'produtos': [_produto_local_to_dict(pl) for pl in qs]})

    data = json.loads(request.body)
    local_id = data.get('localId')
    produto_id = data.get('produtoId')
    if not local_id or not produto_id:
        return _json_error('localId e produtoId são obrigatórios.')

    try:
        local = LocalVenda.objects.get(pk=local_id)
        produto = Produto.objects.get(pk=produto_id)
    except (LocalVenda.DoesNotExist, Produto.DoesNotExist) as e:
        return _json_error(str(e), 404)

    familia = None
    if data.get('familiaId'):
        try:
            familia = FamiliaVenda.objects.get(pk=data['familiaId'], local=local)
        except FamiliaVenda.DoesNotExist:
            return _json_error('Família não encontrada neste local.', 404)

    pl, created = ProdutoLocal.objects.get_or_create(
        produto=produto, local=local,
        defaults={
            'familia': familia,
            'preco_venda': Decimal(str(data.get('preco_venda', '0'))),
            'estoque_minimo': Decimal(str(data.get('estoque_minimo', '0'))),
            'ponto_reabastecimento': Decimal(str(data.get('ponto_reabastecimento', '0'))),
            'estoque_maximo': Decimal(str(data.get('estoque_maximo', '0'))),
        }
    )
    if not created:
        return _json_error('Produto já vinculado a este local.', 409)
    return JsonResponse({'produto_local': _produto_local_to_dict(pl)}, status=201)


@login_required
@require_http_methods(['PUT', 'DELETE'])
def api_produto_local_detail(request, pl_id):
    try:
        pl = ProdutoLocal.objects.select_related('produto', 'familia').get(pk=pl_id)
    except ProdutoLocal.DoesNotExist:
        return _json_error('ProdutoLocal não encontrado.', 404)

    if request.method == 'DELETE':
        pl.delete()
        return _json_ok()

    data = json.loads(request.body)
    for campo in ('preco_venda', 'estoque_atual', 'estoque_minimo',
                  'ponto_reabastecimento', 'estoque_maximo', 'ativo'):
        if campo in data:
            setattr(pl, campo, Decimal(str(data[campo])) if campo != 'ativo' else data[campo])
    if 'familiaId' in data:
        try:
            pl.familia = FamiliaVenda.objects.get(pk=data['familiaId'], local=pl.local)
        except FamiliaVenda.DoesNotExist:
            return _json_error('Família não encontrada.', 404)
    pl.save()
    return JsonResponse({'produto_local': _produto_local_to_dict(pl)})


# ---------------------------------------------------------------------------
# API: Entrada de Estoque Local
# ---------------------------------------------------------------------------

@require_POST
@login_required
@transaction.atomic
def api_entrada_estoque_local(request):
    data = json.loads(request.body)
    pl_id = data.get('produtoLocalId')
    quantidade = Decimal(str(data.get('quantidade', '0')))
    preco_custo = Decimal(str(data.get('preco_custo', '0')))
    preco_venda = Decimal(str(data.get('preco_venda', '0')))
    data_entrada = data.get('data')

    if not pl_id or quantidade <= 0:
        return _json_error('produtoLocalId e quantidade > 0 são obrigatórios.')

    try:
        pl = ProdutoLocal.objects.select_for_update().get(pk=pl_id)
    except ProdutoLocal.DoesNotExist:
        return _json_error('ProdutoLocal não encontrado.', 404)

    entrada = EntradaEstoqueLocal.objects.create(
        produto_local=pl,
        quantidade=quantidade,
        preco_custo=preco_custo,
        preco_venda=preco_venda,
        data=data_entrada or timezone.now().date(),
        observacao=data.get('observacao', ''),
        criado_por=request.user,
    )

    pl.estoque_atual += quantidade
    if preco_venda > 0:
        pl.preco_venda = preco_venda
    pl.save()

    return JsonResponse({'entrada_id': entrada.id, 'estoque_atual': float(pl.estoque_atual)}, status=201)


# ---------------------------------------------------------------------------
# API: Vendas
# ---------------------------------------------------------------------------

@login_required
@require_http_methods(['GET', 'POST'])
def api_vendas(request):
    if request.method == 'GET':
        evento_id = request.GET.get('eventoId')
        local_id = request.GET.get('localId')
        qs = VendaMobile.objects.prefetch_related('itens', 'pagamentos').select_related('local', 'vendedor')
        if evento_id:
            qs = qs.filter(evento_id=evento_id)
        if local_id:
            qs = qs.filter(local_id=local_id)
        return JsonResponse({'vendas': [_venda_to_dict(v) for v in qs]})

    # POST: registrar nova venda
    return _api_post_venda(request)


@transaction.atomic
def _api_post_venda(request):
    data = json.loads(request.body)
    evento_id = data.get('eventoId')
    local_id = data.get('localId')
    total = Decimal(str(data.get('total', '0')))
    itens = data.get('itens', [])
    pagamentos = data.get('pagamentos', [])

    if not evento_id or total <= 0 or not itens:
        return _json_error('eventoId, total > 0 e itens são obrigatórios.')

    try:
        evento = Evento.objects.get(pk=evento_id)
    except Evento.DoesNotExist:
        return _json_error('Evento não encontrado.', 404)

    local = None
    if local_id:
        try:
            local = LocalVenda.objects.get(pk=local_id)
        except LocalVenda.DoesNotExist:
            return _json_error('Local não encontrado.', 404)

    # Gerar ID de referência único
    id_ref = str(uuid.uuid4())[:12].upper()

    # Determinar forma de pagamento principal (para compatibilidade)
    forma_principal = 'MISTO'
    if len(pagamentos) == 1:
        forma_principal = pagamentos[0].get('tipo', 'MISTO')

    venda = VendaMobile.objects.create(
        id_referencia=id_ref,
        evento=evento,
        local=local,
        vendedor=request.user,
        total=total,
        forma_pagamento=forma_principal,
    )

    # Pagamentos
    for pgto in pagamentos:
        valor_pgto = Decimal(str(pgto.get('valor', '0')))
        if valor_pgto > 0:
            PagamentoVenda.objects.create(
                venda=venda,
                tipo=pgto.get('tipo', 'DINHEIRO'),
                valor=valor_pgto,
            )

    # Itens + baixa de estoque
    for item in itens:
        pl_id = item.get('produto_local_id')
        qtd = int(item.get('quantidade', 0))
        preco_unit = Decimal(str(item.get('preco_unitario', '0')))
        desc_perc = Decimal(str(item.get('desconto_perc', '0')))
        total_item = Decimal(str(item.get('total_item', '0')))

        if qtd <= 0:
            continue

        produto_local = None
        nome_produto = item.get('nome', '')
        codigo_produto = item.get('codigo', '')
        familia_produto = item.get('familia', '')

        if pl_id:
            try:
                produto_local = ProdutoLocal.objects.select_for_update().get(pk=pl_id)
                nome_produto = produto_local.produto.nome
                codigo_produto = produto_local.produto.sku
                familia_produto = produto_local.familia.nome if produto_local.familia else ''
                produto_local.aplicar_saida(qtd)
                produto_local.save(update_fields=['estoque_atual'])
            except ProdutoLocal.DoesNotExist:
                return _json_error(f'ProdutoLocal {pl_id} não encontrado.')

        ItemVendaMobile.objects.create(
            venda=venda,
            produto_local=produto_local,
            nome_produto=nome_produto,
            codigo_produto=codigo_produto,
            familia_produto=familia_produto,
            quantidade=qtd,
            preco_unitario=preco_unit,
            desconto_perc=desc_perc,
            total_item=total_item,
        )

    # Lançamento financeiro
    try:
        categoria, _ = CategoriaFinanceira.objects.get_or_create(
            nome='Vendas PDV',
            defaults={'tipo': CategoriaFinanceira.RECEITA}
        )
        conta, _ = ContaCaixa.objects.get_or_create(
            nome='Caixa PDV',
            defaults={'ativo': True}
        )
        LancamentoFinanceiro.objects.create(
            evento=evento,
            tipo=LancamentoFinanceiro.RECEITA,
            categoria=categoria,
            conta=conta,
            data=venda.data_hora.date(),
            descricao=f'Venda PDV #{id_ref} — {local.nome if local else ""}',
            valor=total,
            forma_pagamento=LancamentoFinanceiro.PIX if forma_principal == 'PIX' else LancamentoFinanceiro.DINHEIRO,
            criado_por=request.user,
        )
    except Exception:
        pass  # Não bloqueia a venda se o financeiro falhar

    return JsonResponse({'ok': True, 'venda_id': id_ref, 'venda': _venda_to_dict(venda)}, status=201)


@login_required
@require_http_methods(['DELETE'])
@transaction.atomic
def api_venda_detail(request, venda_id):
    try:
        venda = VendaMobile.objects.prefetch_related('itens__produto_local').get(pk=venda_id)
    except VendaMobile.DoesNotExist:
        return _json_error('Venda não encontrada.', 404)

    # Restaurar estoque
    for item in venda.itens.all():
        if item.produto_local_id:
            try:
                pl = ProdutoLocal.objects.select_for_update().get(pk=item.produto_local_id)
                pl.estoque_atual += Decimal(item.quantidade)
                pl.save(update_fields=['estoque_atual'])
            except ProdutoLocal.DoesNotExist:
                pass

    venda.delete()
    return _json_ok()


# ---------------------------------------------------------------------------
# VIEW LEGADA (compatibilidade com pos_mobile)
# ---------------------------------------------------------------------------

@login_required
def pos_mobile_view(request):
    """Redireciona para o novo PDV SPA para substituir a implementação antiga."""
    return redirect('pos:pdv')

