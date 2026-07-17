import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
import base64
import uuid

from apps.core.models import Evento
from apps.finance.models import LancamentoFinanceiro, CategoriaFinanceira, ContaCaixa

@login_required
def caixa_mobile_view(request):
    """Renderiza a aplicacao SPA PWA do Caixa Mobile."""
    return render(request, 'finance/caixa_mobile.html')

@require_GET
@login_required
def api_dados_iniciais(request):
    """Retorna Eventos, Operador e os Lançamentos do dia/operador logado."""
    eventos = Evento.objects.filter(ativo=True).exclude(status=Evento.ENCERRADO)
    if not eventos.exists():
        eventos = Evento.objects.filter(ativo=True)
        
    lista_eventos = [{'id': e.id, 'nome': str(e)} for e in eventos]
    
    # Busca Categorias
    categorias_rec = CategoriaFinanceira.objects.filter(tipo=CategoriaFinanceira.RECEITA)
    categorias_des = CategoriaFinanceira.objects.filter(tipo=CategoriaFinanceira.DESPESA)
    lista_categorias = {
        'Receita': [{'id': c.id, 'nome': str(c.nome)} for c in categorias_rec],
        'Despesa': [{'id': c.id, 'nome': str(c.nome)} for c in categorias_des],
    }
    
    # Pega ultimos 50 lancamentos para aparecer no historico
    lancamentos_bd = LancamentoFinanceiro.objects.filter(criado_por=request.user).order_by('-criado_em')[:50]
    lista_lancamentos = []
    
    for l in lancamentos_bd:
        anexo = l.anexolancamento_set.first()
        anexo_url = anexo.arquivo.url if anexo and anexo.arquivo else l.assinatura_b64
        
        lista_lancamentos.append({
            'id': l.id,
            'evento': l.evento.nome,
            'tipo': 'Receita' if l.tipo == LancamentoFinanceiro.RECEITA else 'Despesa',
            'setor': l.setor_origem or '-',
            'pessoa': l.pessoa or 'Não informado',
            'valor': float(l.valor),
            'descricao': l.descricao,
            'assinatura': anexo_url,
            'data': l.data.strftime('%d/%m/%Y %H:%M')
        })
        
    return JsonResponse({
        'operador': request.user.username,
        'eventos': lista_eventos,
        'categorias': lista_categorias,
        'lancamentos': lista_lancamentos
    })

@require_POST
@login_required
@transaction.atomic
def api_salvar_lancamento(request):
    """Recebe o POST do aplicativo e salva no banco de dados."""
    try:
        data = json.loads(request.body)
        evento_id = data.get('eventoId')
        tipo = data.get('tipo')
        categoria_id = data.get('categoriaId')
        pessoa = data.get('pessoa', '')
        valor = data.get('valor', 0)
        descricao = data.get('descricao', '')
        assinatura_b64 = data.get('assinatura')
        
        evento = Evento.objects.get(pk=evento_id)
        categoria = CategoriaFinanceira.objects.get(pk=categoria_id)
        
        conta, _ = ContaCaixa.objects.get_or_create(nome='Caixa Central', defaults={'ativo': True})
        
        from django.utils.timezone import now
        
        lanc = LancamentoFinanceiro.objects.create(
            evento=evento,
            tipo=CategoriaFinanceira.RECEITA if tipo == 'Receita' else CategoriaFinanceira.DESPESA,
            categoria=categoria,
            conta=conta,
            data=now().date(),
            descricao=descricao if descricao else f"Aporte via Caixa Mobile ({categoria.nome})",
            valor=valor,
            forma_pagamento=LancamentoFinanceiro.OUTRO,
            criado_por=request.user,
            setor_origem=categoria.nome,
            pessoa=pessoa,
            assinatura_b64=assinatura_b64
        )
        
        # Salva o Anexo Financeiro fisico para aparecer no painel principal
        if assinatura_b64 and assinatura_b64.startswith('data:image'):
            try:
                # ex: data:image/jpeg;base64,.....
                formato, imgstr = assinatura_b64.split(';base64,')
                ext = formato.split('/')[-1]
                data_img = base64.b64decode(imgstr)
                nome_arquivo = f"assinatura_{uuid.uuid4().hex}.{ext}"
                
                from apps.finance.models import AnexoLancamento
                AnexoLancamento.objects.create(
                    lancamento=lanc,
                    descricao="Assinatura Eletrônica (Caixa Mobile)",
                    enviado_por=request.user,
                    arquivo=ContentFile(data_img, name=nome_arquivo)
                )
            except Exception as e:
                pass # Evita falhar a gravacao so por causa de anexo quebrado
        
        return JsonResponse({'success': True, 'lancamento_id': lanc.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
