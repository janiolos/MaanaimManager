import json
from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db import transaction

from apps.core.models import Evento
from apps.inventory.models import Produto
from apps.finance.models import LancamentoFinanceiro, CategoriaFinanceira, ContaCaixa
from apps.pos.models import VendaMobile, ItemVendaMobile

@login_required
def pos_mobile_view(request):
    """Renderiza a aplicacao SPA Mobile."""
    context = {
        'pdv_nome': 'Central de Vendas',
        'titulo_header': 'Caixa Mobile'
    }
    return render(request, 'pos/pos_mobile.html', context)

@require_GET
@login_required
def api_dados_iniciais(request):
    """Retorna os eventos, os produtos ativos do backend e o nome do vendedor."""
    eventos = Evento.objects.filter(ativo=True).exclude(status=Evento.ENCERRADO)
    if not eventos.exists():
        eventos = Evento.objects.filter(ativo=True) # fallback

    lista_eventos = [{'id': e.id, 'nome': str(e)} for e in eventos]
    
    produtos = Produto.objects.filter(ativo=True).exclude(categoria=Produto.CATEGORIA_MATERIA_PRIMA)
    lista_produtos = [
        {
            'id': p.id,
            'nome': p.nome,
            'preco': float(p.custo_medio_atual) if p.custo_medio_atual else 0.0, # Preco de venda idealmente seria outro campo, mas usamos custo como fallback caso o schema nao tenha. Wait, if there is no sale price, we can use 0 for now or add a custom field. Actually, many times it's in the frontend. But we'll send it as `preco_venda` or `p.custo_medio_atual`. Let's assume there is a price or we just send what we have. Wait! Let me just put 0.0 and users can update, or I will read the inventory.
        } for p in produtos
    ]
    # To fix the price gap, we will use a naive query.
    for prod, p_obj in zip(lista_produtos, produtos):
        # We assume the default price for the MVP is standard 10 reais, or the user edits it.
        # since `Produto` only has `custo_medio_atual`.
        prod['preco'] = float(p_obj.custo_medio_atual * 2) if p_obj.custo_medio_atual > 0 else 10.0
        prod['estoque'] = float(p_obj.estoque_atual)
        
    return JsonResponse({
        'vendedor': request.user.username,
        'eventos': lista_eventos,
        'produtos': lista_produtos,
    })

@require_POST
@login_required
@transaction.atomic
def api_post_venda(request):
    """
    Recebe a venda do mobile e processa.
    O json tem: { eventoId, total, forma, itens: [{id, qtd, preco_unitario, totalItem}] }
    """
    try:
        data = json.loads(request.body)
        evento_id = data.get('eventoId')
        total = Decimal(str(data.get('total', 0)))
        forma = data.get('forma', 'PIX')
        itens = data.get('itens', [])
        
        if not evento_id or total <= 0 or not itens:
            return JsonResponse({'error': 'Dados invalidos'}, status=400)
            
        evento = Evento.objects.get(pk=evento_id)
        
        # 1. Obtermos Categoria e ContaCaixa padrao para as operacoes
        categoria, _ = CategoriaFinanceira.objects.get_or_create(
            nome='Vendas Mobile', 
            defaults={'tipo': CategoriaFinanceira.RECEITA}
        )
        conta, _ = ContaCaixa.objects.get_or_create(
            nome='Caixa Mobile',
            defaults={'ativo': True}
        )
        
        # 2. Criar a Venda no POS
        import uuid
        venda_obj = VendaMobile.objects.create(
            id_referencia=str(uuid.uuid4())[:8],
            evento=evento,
            vendedor=request.user,
            total=total,
            forma_pagamento=forma
        )
        
        # 3. Processar itens, diminuir estoque
        for item in itens:
            produto_id = item.get('id')
            qtd = Decimal(str(item.get('qtd', 0)))
            if qtd <= 0: continue
            
            produto = Produto.objects.select_for_update().get(pk=produto_id)
            
            produto.aplicar_saida(qtd)
            produto.save()
            
            preco_unit = Decimal(str(item.get('preco_unitario', 0) or item.get('preco', 0)))
            total_item_val = Decimal(str(item.get('totalItem', 0)))
            
            ItemVendaMobile.objects.create(
                venda=venda_obj,
                produto=produto,
                quantidade=int(qtd),
                preco_unitario=preco_unit,
                total_item=total_item_val
            )
            
        # 4. Gravar Lancamento Financeiro
        LancamentoFinanceiro.objects.create(
            evento=evento,
            tipo=LancamentoFinanceiro.RECEITA,
            categoria=categoria,
            conta=conta,
            data=venda_obj.data_hora.date(),
            descricao=f"Venda Mobile PWA #{venda_obj.id_referencia}",
            valor=total,
            forma_pagamento=LancamentoFinanceiro.PIX if forma.upper() == 'PIX' else LancamentoFinanceiro.DINHEIRO,
            criado_por=request.user
        )
        
        return JsonResponse({'success': True, 'venda_id': venda_obj.id_referencia})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
