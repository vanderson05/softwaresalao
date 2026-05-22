# agenda/views.py

from datetime import date as date_type, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from tenants.permissions import (
    TenantAccessPermission,
    IsOwnerOrManager,
    check_professional_limit,
)
from .models import Professional, Service, Schedule, ScheduleBlock
from .serializers import (
    ProfessionalSerializer,
    ProfessionalListSerializer,
    ServiceSerializer,
    ScheduleSerializer,
    ScheduleBulkSerializer,
    ScheduleBlockSerializer,
)
from .slots import get_available_slots, get_next_available_slots


# ════════════════════════════════════════════════════════════════
# PROFISSIONAIS
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def professionals_view(request):
    """
    GET  /api/professionals/  → lista profissionais ativos do tenant
    POST /api/professionals/  → cria profissional (valida limite do plano)
    """
    tenant = request.tenant

    if request.method == 'GET':
        professionals = Professional.objects.filter(
            tenant=tenant, is_active=True
        ).order_by('name')
        serializer = ProfessionalListSerializer(professionals, many=True)
        return Response(serializer.data)

    # POST
    if request.tenant_role not in ('owner', 'manager'):
        return Response(
            {'error': 'Apenas donos e gerentes podem cadastrar profissionais.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Valida limite do plano
    check_professional_limit(tenant)

    serializer = ProfessionalSerializer(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save(tenant=tenant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def professional_detail_view(request, professional_id):
    """
    GET    /api/professionals/{id}/  → detalhes do profissional
    PUT    /api/professionals/{id}/  → atualiza completo
    PATCH  /api/professionals/{id}/  → atualiza parcial
    DELETE /api/professionals/{id}/  → desativa (soft delete)
    """
    tenant = request.tenant

    try:
        professional = Professional.objects.get(
            id=professional_id, tenant=tenant
        )
    except Professional.DoesNotExist:
        return Response({'error': 'Profissional não encontrado.'}, status=404)

    if request.method == 'GET':
        serializer = ProfessionalSerializer(professional)
        data = serializer.data
        # Inclui serviços do profissional
        from .serializers import ServiceSerializer
        data['services'] = ServiceSerializer(
            professional.get_services(), many=True,
            context={'request': request}
        ).data
        return Response(data)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method in ('PUT', 'PATCH'):
        partial    = request.method == 'PATCH'
        serializer = ProfessionalSerializer(
            professional, data=request.data,
            partial=partial, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    if request.method == 'DELETE':
        professional.is_active = False
        professional.save(update_fields=['is_active'])
        return Response({'message': 'Profissional desativado.'}, status=200)


# ════════════════════════════════════════════════════════════════
# SERVIÇOS
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def services_view(request):
    """
    GET  /api/services/  → lista serviços ativos
    POST /api/services/  → cria serviço
    """
    tenant = request.tenant

    if request.method == 'GET':
        services   = Service.objects.filter(
            tenant=tenant, is_active=True
        ).prefetch_related('professionals')
        serializer = ServiceSerializer(
            services, many=True, context={'request': request}
        )
        return Response(serializer.data)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    serializer = ServiceSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save(tenant=tenant)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def service_detail_view(request, service_id):
    """CRUD completo de serviço."""
    tenant = request.tenant

    try:
        service = Service.objects.get(id=service_id, tenant=tenant)
    except Service.DoesNotExist:
        return Response({'error': 'Serviço não encontrado.'}, status=404)

    if request.method == 'GET':
        serializer = ServiceSerializer(service, context={'request': request})
        return Response(serializer.data)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method in ('PUT', 'PATCH'):
        partial    = request.method == 'PATCH'
        serializer = ServiceSerializer(
            service, data=request.data,
            partial=partial, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    if request.method == 'DELETE':
        service.is_active = False
        service.save(update_fields=['is_active'])
        return Response({'message': 'Serviço desativado.'}, status=200)


# ════════════════════════════════════════════════════════════════
# HORÁRIOS (SCHEDULES)
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def schedules_view(request, professional_id):
    """
    GET  /api/professionals/{id}/schedules/  → horários do profissional
    POST /api/professionals/{id}/schedules/  → define horário de um dia
    """
    tenant = request.tenant

    try:
        professional = Professional.objects.get(
            id=professional_id, tenant=tenant, is_active=True
        )
    except Professional.DoesNotExist:
        return Response({'error': 'Profissional não encontrado.'}, status=404)

    if request.method == 'GET':
        schedules  = Schedule.objects.filter(professional=professional)
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    serializer = ScheduleSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        # Upsert — atualiza se já existe para esse dia
        Schedule.objects.update_or_create(
            professional=professional,
            weekday=serializer.validated_data['weekday'],
            defaults={
                'tenant':     tenant,
                'start_time': serializer.validated_data['start_time'],
                'end_time':   serializer.validated_data['end_time'],
                'is_active':  True,
            }
        )
        return Response(
            ScheduleSerializer(
                Schedule.objects.get(
                    professional=professional,
                    weekday=serializer.validated_data['weekday']
                )
            ).data,
            status=201
        )

    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def schedules_bulk_view(request):
    """
    POST /api/schedules/bulk/
    Configura múltiplos dias de uma vez — usado no wizard de setup.

    Payload:
    {
        "professional_id": "uuid",
        "schedules": [
            {"weekday": 0, "start_time": "13:00", "end_time": "18:00"},
            {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
            ...
        ]
    }
    """
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    serializer = ScheduleBulkSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        result = serializer.save()
        return Response({
            'message': 'Horários configurados com sucesso.',
            'created': result['created'],
            'updated': result['updated'],
        }, status=200)

    return Response(serializer.errors, status=400)


# ════════════════════════════════════════════════════════════════
# BLOQUEIOS
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def schedule_blocks_view(request, professional_id):
    """
    GET  /api/professionals/{id}/blocks/  → bloqueios do profissional
    POST /api/professionals/{id}/blocks/  → cria bloqueio
    """
    tenant = request.tenant

    try:
        professional = Professional.objects.get(
            id=professional_id, tenant=tenant
        )
    except Professional.DoesNotExist:
        return Response({'error': 'Profissional não encontrado.'}, status=404)

    if request.method == 'GET':
        blocks     = ScheduleBlock.objects.filter(professional=professional)
        serializer = ScheduleBlockSerializer(blocks, many=True)
        return Response(serializer.data)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    serializer = ScheduleBlockSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save(tenant=tenant, professional=professional)
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


# ════════════════════════════════════════════════════════════════
# SLOTS DISPONÍVEIS
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def slots_view(request):
    """
    GET /api/slots/?service_id=xxx&date=2026-05-22&professional_id=xxx

    professional_id é opcional — se não informado retorna slots
    de todos os profissionais que realizam o serviço.
    """
    tenant = request.tenant

    service_id      = request.query_params.get('service_id')
    date_str        = request.query_params.get('date')
    professional_id = request.query_params.get('professional_id')

    if not service_id:
        return Response({'error': 'service_id obrigatório.'}, status=400)

    if not date_str:
        return Response({'error': 'date obrigatório (YYYY-MM-DD).'}, status=400)

    try:
        query_date = date_type.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'date inválido. Use YYYY-MM-DD.'}, status=400)

    try:
        service = Service.objects.get(
            id=service_id, tenant=tenant, is_active=True
        )
    except Service.DoesNotExist:
        return Response({'error': 'Serviço não encontrado.'}, status=404)

    # Com profissional específico
    if professional_id:
        try:
            professional = Professional.objects.get(
                id=professional_id, tenant=tenant, is_active=True
            )
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado.'}, status=404)

        slots = get_available_slots(professional, service, query_date)
        return Response({
            'date':         date_str,
            'professional': {'id': str(professional.id), 'name': professional.name},
            'service':      {'id': str(service.id), 'name': service.name, 'duration_min': service.duration_min},
            'slots':        slots,
        })

    # Sem profissional — retorna de todos que realizam o serviço
    professionals = Professional.objects.filter(
        tenant=tenant, is_active=True
    )
    result = []
    for prof in professionals:
        if not prof.get_services().filter(id=service.id).exists():
            continue
        slots = get_available_slots(prof, service, query_date)
        if slots:
            result.append({
                'professional': {'id': str(prof.id), 'name': prof.name},
                'slots': slots,
            })

    return Response({
        'date':    date_str,
        'service': {'id': str(service.id), 'name': service.name},
        'results': result,
    })


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def next_slots_view(request):
    """
    GET /api/slots/next/?service_id=xxx&days=7

    Retorna os próximos slots disponíveis para um serviço
    em qualquer profissional, nos próximos N dias.
    Usado pelo agente WhatsApp.
    """
    tenant     = request.tenant
    service_id = request.query_params.get('service_id')
    days       = int(request.query_params.get('days', 7))

    if not service_id:
        return Response({'error': 'service_id obrigatório.'}, status=400)

    try:
        service = Service.objects.get(
            id=service_id, tenant=tenant, is_active=True
        )
    except Service.DoesNotExist:
        return Response({'error': 'Serviço não encontrado.'}, status=404)

    slots = get_next_available_slots(tenant, service, days_ahead=days)

    return Response({
        'service': {'id': str(service.id), 'name': service.name},
        'days_ahead': days,
        'slots': slots,
    })