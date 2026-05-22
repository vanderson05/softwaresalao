# agenda/views_appointment.py
# Adicionar ao agenda/views.py

from datetime import date as date_type, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from tenants.permissions import TenantAccessPermission
from .models import Appointment, Professional, Service
from .serializers_appointment import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AppointmentListSerializer,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_appointment(appointment_id, tenant):
    try:
        return Appointment.objects.get(id=appointment_id, tenant=tenant)
    except Appointment.DoesNotExist:
        return None


def _trigger_completed(appointment):
    """
    Gatilho ao completar agendamento:
    1. Gera CashEntry (financeiro)
    2. Atualiza last_visit_at do cliente
    3. Dispara NPS se feature ativa
    """
    tenant = appointment.tenant

    # 1. Gera CashEntry
    try:
        from financial.models import CashEntry
        CashEntry.objects.get_or_create(
            appointment=appointment,
            defaults={
                'tenant':       tenant,
                'professional': appointment.professional,
                'amount':       appointment.price_snapshot or appointment.service.price,
            }
        )
    except Exception as e:
        print(f"[CASHENTRY ERROR] {e}")

    # 2. Atualiza last_visit_at do cliente
    if appointment.client:
        try:
            appointment.client.last_visit_at = timezone.now()
            appointment.client.save(update_fields=['last_visit_at'])
        except Exception as e:
            print(f"[CLIENT UPDATE ERROR] {e}")

    # 3. NPS — marca para envio pelo job (não envia aqui direto)
    if tenant.has_feature('nps') and not appointment.nps_sent:
        appointment.nps_sent = False  # job vai processar
        appointment.save(update_fields=['nps_sent'])


# ════════════════════════════════════════════════════════════════
# CRUD PRINCIPAL
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def appointments_view(request):
    """
    GET  /api/appointments/  → lista agendamentos com filtros
    POST /api/appointments/  → cria agendamento (3 canais)

    Filtros GET:
      ?date=2026-05-22
      ?professional_id=uuid
      ?status=pending,confirmed,completed,cancelled,no_show
      ?source=whatsapp,panel,link
    """
    tenant = request.tenant

    if request.method == 'GET':
        qs = Appointment.objects.filter(tenant=tenant).select_related(
            'professional', 'service', 'client'
        )

        # Filtro por data
        date_str = request.query_params.get('date')
        if date_str:
            try:
                filter_date = date_type.fromisoformat(date_str)
                qs = qs.filter(starts_at__date=filter_date)
            except ValueError:
                return Response({'error': 'date inválido. Use YYYY-MM-DD.'}, status=400)

        # Filtro por profissional
        professional_id = request.query_params.get('professional_id')
        if professional_id:
            qs = qs.filter(professional_id=professional_id)

        # Filtro por status
        status_filter = request.query_params.get('status')
        if status_filter:
            statuses = [s.strip() for s in status_filter.split(',')]
            qs = qs.filter(status__in=statuses)

        # Filtro por source
        source_filter = request.query_params.get('source')
        if source_filter:
            sources = [s.strip() for s in source_filter.split(',')]
            qs = qs.filter(source__in=sources)

        serializer = AppointmentListSerializer(qs.order_by('starts_at'), many=True)
        return Response(serializer.data)

    # POST — cria agendamento
    serializer = AppointmentCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid():
        appointment = serializer.save()
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def appointment_detail_view(request, appointment_id):
    """GET /api/appointments/{id}/ → detalhes do agendamento"""
    appointment = _get_appointment(appointment_id, request.tenant)
    if not appointment:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)
    return Response(AppointmentSerializer(appointment).data)


# ════════════════════════════════════════════════════════════════
# AÇÕES DE STATUS
# ════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def appointment_confirm_view(request, appointment_id):
    """
    POST /api/appointments/{id}/confirm/
    Barbeiro confirma agendamento pendente.
    """
    appointment = _get_appointment(appointment_id, request.tenant)
    if not appointment:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)

    if appointment.status != Appointment.Status.PENDING:
        return Response({
            'error': f"Não é possível confirmar um agendamento com status '{appointment.get_status_display()}'."
        }, status=400)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    appointment.status = Appointment.Status.CONFIRMED
    appointment.save(update_fields=['status', 'updated_at'])

    return Response({
        'message':    'Agendamento confirmado.',
        'status':     appointment.status,
        'id':         str(appointment.id),
        'client':     appointment.client_name,
        'starts_at':  appointment.starts_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def appointment_cancel_view(request, appointment_id):
    """
    POST /api/appointments/{id}/cancel/
    Cancela agendamento.

    Quem pode cancelar:
    - Barbeiro (owner/manager): cancela sem informar phone
    - Cliente: DEVE informar client_phone — validado contra o agendamento
      Se vier client_phone no body, sempre valida — mesmo sendo owner.
    """
    appointment = _get_appointment(appointment_id, request.tenant)
    if not appointment:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)

    if appointment.status in (
        Appointment.Status.COMPLETED,
        Appointment.Status.CANCELLED,
        Appointment.Status.NO_SHOW,
    ):
        return Response({
            'error': f"Não é possível cancelar um agendamento com status '{appointment.get_status_display()}'."
        }, status=400)

    client_phone = request.data.get('client_phone', '').strip()
    is_staff     = request.tenant_role in ('owner', 'manager')

    # Se client_phone foi informado → valida sempre (cliente cancelando)
    if client_phone:
        if not appointment.client_phone or client_phone != appointment.client_phone:
            return Response({
                'error': 'Telefone não confere com o cadastrado no agendamento.',
            }, status=403)
    elif not is_staff:
        # Sem phone e sem ser staff → nega
        return Response({
            'error': 'Informe o telefone cadastrado no agendamento para cancelar.',
        }, status=403)

    reason = request.data.get('reason', '')
    appointment.status = Appointment.Status.CANCELLED
    if reason:
        appointment.notes = f"{appointment.notes}\n[Cancelamento] {reason}".strip()
    appointment.save(update_fields=['status', 'notes', 'updated_at'])

    return Response({
        'message':   'Agendamento cancelado.',
        'status':    appointment.status,
        'id':        str(appointment.id),
        'client':    appointment.client_name,
        'starts_at': appointment.starts_at.isoformat(),
    })


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def appointment_complete_view(request, appointment_id):
    """
    POST /api/appointments/{id}/complete/
    Barbeiro marca atendimento como realizado.
    Gatilho: CashEntry + atualiza cliente + prepara NPS
    """
    appointment = _get_appointment(appointment_id, request.tenant)
    if not appointment:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)

    if appointment.status != Appointment.Status.CONFIRMED:
        return Response({
            'error': f"Apenas agendamentos confirmados podem ser completados. Status atual: '{appointment.get_status_display()}'."
        }, status=400)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    # Permite sobrescrever o valor (desconto, pacote, etc.)
    price = request.data.get('price')
    if price is not None:
        try:
            appointment.price_snapshot = float(price)
        except (ValueError, TypeError):
            return Response({'error': 'price inválido.'}, status=400)

    # Forma de pagamento
    payment_method = request.data.get('payment_method', 'pix')

    appointment.status = Appointment.Status.COMPLETED
    appointment.save(update_fields=['status', 'price_snapshot', 'updated_at'])

    # Atualiza CashEntry com forma de pagamento
    _trigger_completed(appointment)
    try:
        from financial.models import CashEntry
        CashEntry.objects.filter(appointment=appointment).update(
            payment_method=payment_method
        )
    except Exception:
        pass

    return Response({
        'message':        'Atendimento concluído.',
        'status':         appointment.status,
        'id':             str(appointment.id),
        'client':         appointment.client_name,
        'price':          str(appointment.price_snapshot),
        'payment_method': payment_method,
    })


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def appointment_no_show_view(request, appointment_id):
    """
    POST /api/appointments/{id}/no-show/
    Barbeiro marca cliente como não compareceu.
    """
    appointment = _get_appointment(appointment_id, request.tenant)
    if not appointment:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)

    if appointment.status != Appointment.Status.CONFIRMED:
        return Response({
            'error': f"Apenas agendamentos confirmados podem ser marcados como não compareceu."
        }, status=400)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    appointment.status = Appointment.Status.NO_SHOW
    appointment.save(update_fields=['status', 'updated_at'])

    return Response({
        'message': 'Marcado como não compareceu.',
        'status':  appointment.status,
        'id':      str(appointment.id),
        'client':  appointment.client_name,
    })


# ════════════════════════════════════════════════════════════════
# AGENDA DO DIA / SEMANA
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def agenda_day_view(request):
    """
    GET /api/agenda/day/?date=2026-05-22&professional_id=uuid

    Retorna agenda completa do dia agrupada por profissional.
    professional_id opcional — sem ele retorna todos.
    """
    tenant   = request.tenant
    date_str = request.query_params.get('date', date_type.today().isoformat())

    try:
        filter_date = date_type.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'date inválido.'}, status=400)

    professional_id = request.query_params.get('professional_id')

    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    if professional_id:
        professionals = professionals.filter(id=professional_id)

    result = []
    for prof in professionals:
        appointments = Appointment.objects.filter(
            tenant=tenant,
            professional=prof,
            starts_at__date=filter_date,
        ).exclude(
            status=Appointment.Status.CANCELLED
        ).order_by('starts_at')

        result.append({
            'professional': {
                'id':   str(prof.id),
                'name': prof.name,
            },
            'appointments': AppointmentListSerializer(appointments, many=True).data,
            'total': appointments.count(),
        })

    return Response({
        'date':          date_str,
        'professionals': result,
        'total':         sum(p['total'] for p in result),
    })


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def agenda_week_view(request):
    """
    GET /api/agenda/week/?date=2026-05-22

    Retorna resumo da semana (quantidade por dia).
    date = qualquer dia da semana desejada.
    """
    tenant   = request.tenant
    date_str = request.query_params.get('date', date_type.today().isoformat())

    try:
        ref_date = date_type.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'date inválido.'}, status=400)

    # Início e fim da semana (segunda a domingo)
    start = ref_date - timedelta(days=ref_date.weekday())
    end   = start + timedelta(days=6)

    week = []
    for i in range(7):
        day = start + timedelta(days=i)
        count = Appointment.objects.filter(
            tenant=tenant,
            starts_at__date=day,
        ).exclude(status=Appointment.Status.CANCELLED).count()

        week.append({
            'date':     day.isoformat(),
            'weekday':  day.weekday(),
            'count':    count,
        })

    return Response({
        'week_start':    start.isoformat(),
        'week_end':      end.isoformat(),
        'days':          week,
        'total_week':    sum(d['count'] for d in week),
    })