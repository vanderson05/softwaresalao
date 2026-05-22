# agenda/slots.py
# Lógica de geração de slots disponíveis para agendamento
# Usada pelo agente WhatsApp e pelo painel web

from datetime import datetime, timedelta, date as date_type, time as time_type
from django.utils import timezone
from django.db.models import Q


def get_available_slots(professional, service, date) -> list[dict]:
    """
    Retorna lista de slots disponíveis para um profissional + serviço + data.

    Regras:
    1. Profissional deve ter Schedule para o dia da semana
    2. Dia não pode estar totalmente bloqueado (ScheduleBlock dia inteiro)
    3. Slot = max(service.duration_min, professional.slot_interval)
    4. Slot só aparece se duration_min cabe antes do fim do expediente
    5. Slot não pode conflitar com agendamentos existentes
    6. Bloqueios parciais também são considerados

    Retorna:
        [
            {'time': '09:00', 'available': True},
            {'time': '09:30', 'available': True},
            ...
        ]
    """
    from agenda.models import Schedule, ScheduleBlock, Appointment

    # ── 1. Busca o Schedule do dia da semana ──────────────────────────────────
    weekday  = date.weekday()  # 0=segunda, 6=domingo
    schedule = Schedule.objects.filter(
        professional=professional,
        weekday=weekday,
        is_active=True,
    ).first()

    if not schedule:
        return []  # Profissional não trabalha nesse dia

    # ── 2. Verifica bloqueio do dia inteiro ───────────────────────────────────
    full_day_block = ScheduleBlock.objects.filter(
        professional=professional,
        date=date,
        start_time__isnull=True,
    ).exists()

    if full_day_block:
        return []  # Dia inteiro bloqueado

    # ── 3. Busca bloqueios parciais do dia ────────────────────────────────────
    partial_blocks = ScheduleBlock.objects.filter(
        professional=professional,
        date=date,
        start_time__isnull=False,
    ).values_list('start_time', 'end_time')

    # ── 4. Busca agendamentos existentes no dia ───────────────────────────────
    day_start = timezone.make_aware(datetime.combine(date, time_type.min))
    day_end   = timezone.make_aware(datetime.combine(date, time_type.max))

    existing_appointments = Appointment.objects.filter(
        professional=professional,
        starts_at__gte=day_start,
        starts_at__lte=day_end,
        status__in=['pending', 'confirmed'],
    ).values_list('starts_at', 'ends_at')

    # ── 5. Gera os slots ──────────────────────────────────────────────────────
    # Duração real do slot = max(duração do serviço, intervalo do profissional)
    slot_duration = max(service.duration_min, professional.slot_interval)
    step          = professional.slot_interval  # passo de iteração

    slots   = []
    current = schedule.start_time

    while True:
        # Slot termina em current + slot_duration
        slot_start_dt = datetime.combine(date, current)
        slot_end_dt   = slot_start_dt + timedelta(minutes=slot_duration)

        # Para quando o slot não cabe mais no expediente
        if slot_end_dt.time() > schedule.end_time:
            break

        # Verifica conflito com bloqueios parciais
        blocked = False
        for block_start, block_end in partial_blocks:
            if current < block_end and slot_end_dt.time() > block_start:
                blocked = True
                break

        # Verifica conflito com agendamentos existentes
        if not blocked:
            slot_start_aware = timezone.make_aware(slot_start_dt)
            slot_end_aware   = timezone.make_aware(slot_end_dt)

            for appt_start, appt_end in existing_appointments:
                if slot_start_aware < appt_end and slot_end_aware > appt_start:
                    blocked = True
                    break

        # Não retorna slots no passado
        now = timezone.now()
        slot_aware = timezone.make_aware(slot_start_dt)
        if slot_aware <= now:
            blocked = True

        if not blocked:
            slots.append({
                'time':     current.strftime('%H:%M'),
                'datetime': slot_aware.isoformat(),
            })

        # Avança pelo step (slot_interval do profissional)
        next_dt  = slot_start_dt + timedelta(minutes=step)
        current  = next_dt.time()

        if current >= schedule.end_time:
            break

    return slots


def get_available_slots_by_date_range(professional, service, start_date, end_date) -> dict:
    """
    Retorna slots disponíveis para um intervalo de datas.
    Útil para o agente WhatsApp mostrar opções dos próximos dias.

    Retorna:
        {
            '2026-05-22': [{'time': '09:00', ...}, ...],
            '2026-05-23': [],
            ...
        }
    """
    result      = {}
    current     = start_date
    delta       = timedelta(days=1)

    while current <= end_date:
        slots = get_available_slots(professional, service, current)
        result[current.isoformat()] = slots
        current += delta

    return result


def get_next_available_slots(tenant, service, days_ahead=7) -> list[dict]:
    """
    Retorna os próximos slots disponíveis para um serviço em qualquer
    profissional que o realize, nos próximos N dias.
    Usado pelo agente quando cliente não tem preferência de profissional.

    Retorna:
        [
            {
                'professional': {'id': ..., 'name': 'Carlão'},
                'date': '2026-05-22',
                'time': '09:00',
                'datetime': '...',
            },
            ...
        ]
    """
    from agenda.models import Professional

    results     = []
    today       = timezone.localdate()
    professionals = Professional.objects.filter(
        tenant=tenant, is_active=True
    )

    for professional in professionals:
        # Verifica se o profissional realiza este serviço
        services = professional.get_services()
        if not services.filter(id=service.id).exists():
            continue

        for day_offset in range(days_ahead):
            check_date = today + timedelta(days=day_offset)
            slots      = get_available_slots(professional, service, check_date)

            for slot in slots[:3]:  # máx 3 slots por profissional por dia
                results.append({
                    'professional': {
                        'id':   str(professional.id),
                        'name': professional.name,
                    },
                    'date':     check_date.isoformat(),
                    'time':     slot['time'],
                    'datetime': slot['datetime'],
                })

    # Ordena por data e hora
    results.sort(key=lambda x: x['datetime'])
    return results[:20]  # máx 20 opções