from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import ReminderConfig
from .forms import ReminderConfigForm
from apps.core.models import Evento
from apps.core.permissions import can_read_notifications, can_write_notifications


@login_required
@user_passes_test(can_read_notifications)
def lembretes_lista(request):
    """Lista todos os lembretes do evento atual"""
    evento_atual = request.session.get('evento_id')

    if not evento_atual:
        messages.warning(request, 'Selecione um evento primeiro.')
        return redirect('core:selecionar_evento')

    try:
        evento = Evento.objects.get(id=evento_atual)
    except Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('core:selecionar_evento')

    lembretes = ReminderConfig.objects.filter(
        evento=evento).order_by('-criado_em')

    contexto = {
        'lembretes': lembretes,
        'evento': evento,
        'total_lembretes': lembretes.count(),
        'lembretes_ativos': lembretes.filter(ativo=True).count(),
        'lembretes_enviados': lembretes.filter(enviado=True).count(),
    }

    return render(request, 'notifications/lembretes_lista.html', contexto)


@login_required
@user_passes_test(can_write_notifications)
def lembrete_criar(request):
    """Criar novo lembrete"""
    evento_atual = request.session.get('evento_id')

    if not evento_atual:
        messages.warning(request, 'Selecione um evento primeiro.')
        return redirect('core:selecionar_evento')

    try:
        evento = Evento.objects.get(id=evento_atual)
    except Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.')
        return redirect('core:selecionar_evento')

    if request.method == 'POST':
        form = ReminderConfigForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                lembrete = form.save(commit=False)
                lembrete.evento = evento
                lembrete.save()
                messages.success(request, 'Lembrete criado com sucesso!')
                return redirect('notifications:lembretes_lista')
            except Exception as e:
                messages.error(request, f'Erro ao criar lembrete: {str(e)}')
        else:
            # Mostrar erros no log para debug
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Erro em {field}: {error}")
    else:
        form = ReminderConfigForm()

    contexto = {
        'form': form,
        'evento': evento,
        'titulo': 'Novo Lembrete',
    }

    return render(request, 'notifications/lembrete_form.html', contexto)


@login_required
@user_passes_test(can_write_notifications)
def lembrete_editar(request, lembrete_id):
    """Editar um lembrete existente"""
    evento_atual = request.session.get('evento_id')

    if not evento_atual:
        messages.warning(request, 'Selecione um evento primeiro.')
        return redirect('core:selecionar_evento')

    lembrete = get_object_or_404(
        ReminderConfig, id=lembrete_id, evento_id=evento_atual)

    if request.method == 'POST':
        form = ReminderConfigForm(request.POST, request.FILES, instance=lembrete)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Lembrete atualizado com sucesso!')
                return redirect('notifications:lembretes_lista')
            except Exception as e:
                messages.error(
                    request, f'Erro ao atualizar lembrete: {str(e)}')
    else:
        form = ReminderConfigForm(instance=lembrete)

    contexto = {
        'form': form,
        'evento': lembrete.evento,
        'lembrete': lembrete,
        'titulo': 'Editar Lembrete',
    }

    return render(request, 'notifications/lembrete_form.html', contexto)


@login_required
@require_http_methods(["POST"])
@user_passes_test(can_write_notifications)
def lembrete_excluir(request, lembrete_id):
    """Excluir um lembrete"""
    evento_atual = request.session.get('evento_id')

    if not evento_atual:
        messages.warning(request, 'Selecione um evento primeiro.')
        return redirect('core:selecionar_evento')

    lembrete = get_object_or_404(
        ReminderConfig, id=lembrete_id, evento_id=evento_atual)
    lembrete.delete()
    messages.success(request, 'Lembrete excluído com sucesso!')

    return redirect('notifications:lembretes_lista')


@login_required
@require_http_methods(["POST"])
@user_passes_test(can_write_notifications)
def lembrete_resetar(request, lembrete_id):
    """Resetar um lembrete para reenvio"""
    evento_atual = request.session.get('evento_id')

    if not evento_atual:
        messages.warning(request, 'Selecione um evento primeiro.')
        return redirect('core:selecionar_evento')

    lembrete = get_object_or_404(
        ReminderConfig, id=lembrete_id, evento_id=evento_atual)
    lembrete.enviado = False
    lembrete.save()
    messages.success(
        request, f'Lembrete resetado! Será reenviado na próxima oportunidade.')

    return redirect('notifications:lembretes_lista')
