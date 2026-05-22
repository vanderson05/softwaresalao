# ════════════════════════════════════════════════════════════════
# tenants/views_setup.py
# Views do wizard de setup — Passo 1 + conclusão
# ════════════════════════════════════════════════════════════════
 
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
 
from tenants.permissions import TenantAccessPermission, IsOwnerOrManager
from tenants.models import TenantBusinessHours
from tenants.serializers import TenantBasicSerializer
 
 
@api_view(['GET', 'PATCH'])
@permission_classes([TenantAccessPermission])
def setup_establishment_view(request):
    """
    GET   /api/setup/establishment/  → dados atuais do estabelecimento
    PATCH /api/setup/establishment/  → atualiza dados + horários (Passo 1)
    """
    tenant = request.tenant
 
    if request.method == 'GET':
        hours = TenantBusinessHours.objects.filter(tenant=tenant).order_by('weekday')
        return Response({
            'id':       str(tenant.id),
            'name':     tenant.name,
            'type':     tenant.type,
            'phone':    tenant.phone,
            'email':    tenant.email,
            'address':  tenant.address,
            'city':     tenant.city,
            'logo_url': tenant.logo_url,
            'business_hours': [
                {
                    'weekday':    h.weekday,
                    'weekday_display': h.get_weekday_display(),
                    'open_time':  h.open_time.strftime('%H:%M') if h.open_time else None,
                    'close_time': h.close_time.strftime('%H:%M') if h.close_time else None,
                    'is_closed':  h.is_closed,
                }
                for h in hours
            ],
        })
 
    # PATCH
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)
 
    data = request.data
 
    # Atualiza campos do tenant
    updatable = ['name', 'phone', 'address', 'city', 'logo_url']
    changed   = []
    for field in updatable:
        if field in data:
            setattr(tenant, field, data[field])
            changed.append(field)
 
    if changed:
        tenant.save(update_fields=changed + ['updated_at'])
 
    # Atualiza horários de funcionamento
    business_hours = data.get('business_hours', [])
    for hour_data in business_hours:
        weekday   = hour_data.get('weekday')
        is_closed = hour_data.get('is_closed', False)
 
        if weekday is None or weekday not in range(7):
            continue
 
        from datetime import time as time_type
 
        open_time  = None
        close_time = None
 
        if not is_closed:
            open_str  = hour_data.get('open_time')
            close_str = hour_data.get('close_time')
            if open_str:
                parts     = open_str.split(':')
                open_time = time_type(int(parts[0]), int(parts[1]))
            if close_str:
                parts      = close_str.split(':')
                close_time = time_type(int(parts[0]), int(parts[1]))
 
        TenantBusinessHours.objects.update_or_create(
            tenant=tenant,
            weekday=weekday,
            defaults={
                'open_time':  open_time,
                'close_time': close_time,
                'is_closed':  is_closed,
            }
        )
 
    return Response({
        'message': 'Dados do estabelecimento atualizados.',
        'setup_completed': tenant.setup_completed,
    })
 
 
@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def setup_status_view(request):
    """
    GET /api/setup/status/
    Retorna status de cada passo do wizard.
    """
    from agenda.models import Professional, Service, Schedule
 
    tenant = request.tenant
 
    has_address      = bool(tenant.address and tenant.city)
    professionals    = Professional.objects.filter(tenant=tenant, is_active=True)
    has_professional = professionals.exists()
    has_service      = Service.objects.filter(tenant=tenant, is_active=True).exists()
    has_schedule     = Schedule.objects.filter(
        tenant=tenant, is_active=True,
        professional__in=professionals
    ).exists()
 
    steps = [
        {
            'step':      1,
            'title':     'Dados do estabelecimento',
            'completed': has_address,
            'required':  True,
        },
        {
            'step':      2,
            'title':     'Profissionais',
            'completed': has_professional,
            'required':  True,
            'count':     professionals.count(),
        },
        {
            'step':      3,
            'title':     'Serviços',
            'completed': has_service,
            'required':  True,
            'count':     Service.objects.filter(tenant=tenant, is_active=True).count(),
        },
        {
            'step':      4,
            'title':     'Horários de atendimento',
            'completed': has_schedule,
            'required':  True,
        },
    ]
 
    all_done = all(s['completed'] for s in steps)
 
    return Response({
        'setup_completed': tenant.setup_completed,
        'all_steps_done':  all_done,
        'steps':           steps,
    })
 
 
@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def setup_complete_view(request):
    """
    POST /api/setup/complete/
    Conclui o wizard — valida pré-requisitos e marca setup_completed=True.
    """
    from agenda.models import Professional, Service, Schedule
 
    tenant = request.tenant
 
    if tenant.setup_completed:
        return Response({'message': 'Setup já foi concluído.'}, status=200)
 
    errors = []
 
    # Passo 1 — endereço obrigatório
    if not tenant.address or not tenant.city:
        errors.append('Passo 1: Informe o endereço e a cidade do estabelecimento.')
 
    # Passo 2 — pelo menos 1 profissional
    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    if not professionals.exists():
        errors.append('Passo 2: Cadastre pelo menos 1 profissional.')
 
    # Passo 3 — pelo menos 1 serviço
    if not Service.objects.filter(tenant=tenant, is_active=True).exists():
        errors.append('Passo 3: Cadastre pelo menos 1 serviço.')
 
    # Passo 4 — pelo menos 1 profissional com horário
    if not Schedule.objects.filter(
        tenant=tenant, is_active=True, professional__in=professionals
    ).exists():
        errors.append('Passo 4: Configure os horários de atendimento de pelo menos 1 profissional.')
 
    if errors:
        return Response({
            'error':  'setup_incomplete',
            'errors': errors,
        }, status=status.HTTP_400_BAD_REQUEST)
 
    # Tudo ok — conclui o setup
    tenant.setup_completed = True
    tenant.save(update_fields=['setup_completed', 'updated_at'])
 
    return Response({
        'message':         'Setup concluído! Seu estabelecimento está pronto para receber agendamentos.',
        'setup_completed': True,
    }, status=200)