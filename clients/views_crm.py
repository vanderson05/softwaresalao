# clients/views_crm.py
# Central de CRM — listagem, perfil e insights

from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Q, Max
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from tenants.permissions import TenantAccessPermission, require_feature
from clients.models import Client, ClientTenantProfile, ClientSubscription
from agenda.models import Appointment


# ════════════════════════════════════════════════════════════════
# LISTAGEM DE CLIENTES
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def clients_list_view(request):
    """
    GET /api/crm/clients/
    Lista clientes da barbearia com dados do perfil.

    Filtros:
      ?q=nome_ou_telefone
      ?order=name|last_visit|total_spent|total_visits
    """
    tenant = request.tenant

    profiles = ClientTenantProfile.objects.filter(
        tenant=tenant
    ).select_related('client').order_by('client__name')

    # Busca
    q = request.query_params.get('q', '').strip()
    if q:
        profiles = profiles.filter(
            Q(client__name__icontains=q) |
            Q(client__phone__icontains=q)
        )

    # Ordenação
    order = request.query_params.get('order', 'name')
    order_map = {
        'name':        'client__name',
        'last_visit':  '-last_visit_at',
        'total_visits': '-total_visits',
    }
    profiles = profiles.order_by(order_map.get(order, 'client__name'))

    result = []
    for p in profiles:
        result.append({
            'client_id':    str(p.client.id),
            'name':         p.client.name,
            'phone':        p.client.phone,
            'email':        p.client.email,
            'birthdate':    p.birthdate.isoformat() if p.birthdate else None,
            'loyalty_points': p.loyalty_points,
            'total_visits': p.total_visits,
            'total_spent':  float(p.total_spent),
            'last_visit_at': p.last_visit_at.isoformat() if p.last_visit_at else None,
            'notes':        p.notes,
            'since':        p.created_at.date().isoformat(),
        })

    return Response({
        'clients': result,
        'total':   len(result),
    })


@api_view(['GET', 'PATCH'])
@permission_classes([TenantAccessPermission])
def client_detail_view(request, client_id):
    """
    GET   /api/crm/clients/{id}/ → perfil completo + histórico
    PATCH /api/crm/clients/{id}/ → atualiza notas e aniversário
    """
    tenant = request.tenant

    try:
        profile = ClientTenantProfile.objects.select_related('client').get(
            client_id=client_id, tenant=tenant
        )
    except ClientTenantProfile.DoesNotExist:
        return Response({'error': 'Cliente não encontrado.'}, status=404)

    client = profile.client

    if request.method == 'PATCH':
        if request.tenant_role not in ('owner', 'manager'):
            return Response({'error': 'Sem permissão.'}, status=403)

        if 'notes' in request.data:
            profile.notes = request.data['notes']
        if 'birthdate' in request.data:
            profile.birthdate = request.data['birthdate'] or None

        profile.save(update_fields=['notes', 'birthdate'])

        return Response({'message': 'Perfil atualizado.'})

    # GET — perfil completo
    appointments = Appointment.objects.filter(
        tenant=tenant, client=client
    ).select_related('service', 'professional').order_by('-starts_at')[:20]

    # Assinatura ativa
    subscription = ClientSubscription.objects.filter(
        tenant=tenant, client=client, status='active'
    ).first()

    # Pacotes ativos
    from agenda.models import ClientPackage
    packages = ClientPackage.objects.filter(
        tenant=tenant, client=client, status='active'
    ).select_related('package').order_by('-purchased_at')

    return Response({
        'client': {
            'id':       str(client.id),
            'name':     client.name,
            'phone':    client.phone,
            'email':    client.email,
        },
        'profile': {
            'birthdate':      profile.birthdate.isoformat() if profile.birthdate else None,
            'loyalty_points': profile.loyalty_points,
            'total_visits':   profile.total_visits,
            'total_spent':    float(profile.total_spent),
            'last_visit_at':  profile.last_visit_at.isoformat() if profile.last_visit_at else None,
            'notes':          profile.notes,
            'since':          profile.created_at.date().isoformat(),
        },
        'subscription': {
            'id':               str(subscription.id),
            'name':             subscription.name,
            'type':             subscription.type,
            'visits_per_month': subscription.visits_per_month,
            'visits_used':      subscription.visits_used,
            'visits_remaining': subscription.visits_remaining,
            'price':            float(subscription.price),
            'active_until':     subscription.active_until.isoformat() if subscription.active_until else None,
        } if subscription else None,
        'packages': [
            {
                'id':                 str(p.id),
                'package_name':       p.package.name,
                'service':            p.package.service.name,
                'sessions_remaining': p.sessions_remaining,
                'sessions_total':     p.sessions_total,
            }
            for p in packages
        ],
        'appointments': [
            {
                'id':           str(a.id),
                'service':      a.service.name,
                'professional': a.professional.name,
                'starts_at':    a.starts_at.isoformat(),
                'status':       a.status,
                'price':        float(a.price_snapshot or 0),
            }
            for a in appointments
        ],
    })


# ════════════════════════════════════════════════════════════════
# INSIGHTS
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def insight_summary_view(request):
    """
    GET /api/crm/insights/summary/
    Resumo geral do CRM.
    """
    tenant = request.tenant
    today  = timezone.now().date()
    month_start = today.replace(day=1)

    total_clients = ClientTenantProfile.objects.filter(tenant=tenant).count()

    # Novos este mês
    new_this_month = ClientTenantProfile.objects.filter(
        tenant=tenant,
        created_at__date__gte=month_start
    ).count()

    # Ativos (visitaram nos últimos 30 dias)
    active_cutoff = timezone.now() - timedelta(days=30)
    active = ClientTenantProfile.objects.filter(
        tenant=tenant,
        last_visit_at__gte=active_cutoff
    ).count()

    # Inativos (mais de 30 dias sem visita)
    inactive = ClientTenantProfile.objects.filter(
        tenant=tenant,
        last_visit_at__lt=active_cutoff
    ).count()

    # Aniversariantes da semana
    week_end     = today + timedelta(days=7)
    today_month  = today.month
    today_day    = today.day
    week_end_month = week_end.month
    week_end_day   = week_end.day

    birthday_profiles = ClientTenantProfile.objects.filter(
        tenant=tenant,
        birthdate__isnull=False,
    )
    birthdays_week = sum(
        1 for p in birthday_profiles
        if _is_birthday_in_range(p.birthdate, today, week_end)
    )

    # Assinaturas ativas
    active_subscriptions = ClientSubscription.objects.filter(
        tenant=tenant, status='active'
    ).count()

    return Response({
        'total_clients':        total_clients,
        'new_this_month':       new_this_month,
        'active_last_30d':      active,
        'inactive_over_30d':    inactive,
        'birthdays_this_week':  birthdays_week,
        'active_subscriptions': active_subscriptions,
    })


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def insight_inactive_view(request):
    """
    GET /api/crm/insights/inactive/
    Clientes sem visita há X dias.
    ?days=30  (padrão 30, configurável)
    """
    tenant = request.tenant
    days   = int(request.query_params.get('days', 30))
    cutoff = timezone.now() - timedelta(days=days)

    profiles = ClientTenantProfile.objects.filter(
        tenant=tenant,
        last_visit_at__lt=cutoff,
        last_visit_at__isnull=False,
    ).select_related('client').order_by('last_visit_at')

    result = []
    for p in profiles:
        days_absent = (timezone.now() - p.last_visit_at).days
        result.append({
            'client_id':    str(p.client.id),
            'name':         p.client.name,
            'phone':        p.client.phone,
            'last_visit_at': p.last_visit_at.isoformat(),
            'days_absent':  days_absent,
            'total_visits': p.total_visits,
            'total_spent':  float(p.total_spent),
        })

    return Response({
        'inactive_since_days': days,
        'total':   len(result),
        'clients': result,
    })


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def insight_birthdays_view(request):
    """
    GET /api/crm/insights/birthdays/
    Aniversariantes da semana atual.
    """
    tenant   = request.tenant
    today    = timezone.now().date()
    week_end = today + timedelta(days=7)

    profiles = ClientTenantProfile.objects.filter(
        tenant=tenant,
        birthdate__isnull=False,
    ).select_related('client')

    result = []
    for p in profiles:
        if _is_birthday_in_range(p.birthdate, today, week_end):
            birthday_this_year = p.birthdate.replace(year=today.year)
            days_until = (birthday_this_year - today).days
            if days_until < 0:
                days_until += 365

            result.append({
                'client_id':       str(p.client.id),
                'name':            p.client.name,
                'phone':           p.client.phone,
                'birthdate':       p.birthdate.isoformat(),
                'birthday_this_year': birthday_this_year.isoformat(),
                'days_until':      days_until,
                'is_today':        days_until == 0,
                'total_visits':    p.total_visits,
            })

    result.sort(key=lambda x: x['days_until'])

    return Response({
        'period':  f"{today.isoformat()} a {week_end.isoformat()}",
        'total':   len(result),
        'clients': result,
    })


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def insight_top_clients_view(request):
    """
    GET /api/crm/insights/top/
    Top clientes por valor gasto ou visitas.
    ?order=spent|visits (padrão spent)
    ?limit=10
    """
    tenant = request.tenant
    order  = request.query_params.get('order', 'spent')
    limit  = int(request.query_params.get('limit', 10))

    profiles = ClientTenantProfile.objects.filter(
        tenant=tenant
    ).select_related('client')

    result = []
    for p in profiles:
        result.append({
            'client_id':    str(p.client.id),
            'name':         p.client.name,
            'phone':        p.client.phone,
            'total_visits': p.total_visits,
            'total_spent':  float(p.total_spent),
            'last_visit_at': p.last_visit_at.isoformat() if p.last_visit_at else None,
            'loyalty_points': p.loyalty_points,
        })

    if order == 'visits':
        result.sort(key=lambda x: x['total_visits'], reverse=True)
    else:
        result.sort(key=lambda x: x['total_spent'], reverse=True)

    return Response({
        'order':   order,
        'total':   len(result),
        'clients': result[:limit],
    })


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def insight_new_clients_view(request):
    """
    GET /api/crm/insights/new/
    Clientes novos no período.
    ?days=30 (padrão 30)
    """
    tenant = request.tenant
    days   = int(request.query_params.get('days', 30))
    cutoff = timezone.now() - timedelta(days=days)

    profiles = ClientTenantProfile.objects.filter(
        tenant=tenant,
        created_at__gte=cutoff,
    ).select_related('client').order_by('-created_at')

    result = [
        {
            'client_id':  str(p.client.id),
            'name':       p.client.name,
            'phone':      p.client.phone,
            'since':      p.created_at.date().isoformat(),
            'total_visits': p.total_visits,
        }
        for p in profiles
    ]

    return Response({
        'period_days': days,
        'total':       len(result),
        'clients':     result,
    })


# ════════════════════════════════════════════════════════════════
# ASSINATURAS
# ════════════════════════════════════════════════════════════════
@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def subscriptions_view(request):
    tenant = request.tenant

    if request.method == 'GET':
        status_filter = request.query_params.get('status', 'active')
        qs = ClientSubscription.objects.filter(
            tenant=tenant
        ).select_related('client')

        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        return Response([
            {
                'id':               str(s.id),
                'client':           {'id': str(s.client.id), 'name': s.client.name, 'phone': s.client.phone},
                'name':             s.name,
                'type':             s.type,
                'type_display':     s.get_type_display(),
                'visits_per_month': s.visits_per_month,
                'visits_used':      s.visits_used,
                'visits_remaining': s.visits_remaining,
                'price':            float(s.price),
                'status':           s.status,
                'active_from':      str(s.active_from),
                'active_until':     str(s.active_until) if s.active_until else None,
                'can_visit':        s.can_visit,
                'notes':            s.notes,
            }
            for s in qs.order_by('-created_at')
        ])

    # POST
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    client_phone = ''.join(filter(str.isdigit, request.data.get('client_phone', '')))
    if not client_phone:
        return Response({'error': 'client_phone obrigatório.'}, status=400)

    try:
        client = Client.objects.get(phone=client_phone)
    except Client.DoesNotExist:
        name   = request.data.get('client_name', '').strip()
        client = Client.objects.create(phone=client_phone, name=name or client_phone)

    from clients.models import ClientTenantProfile
    ClientTenantProfile.objects.get_or_create(client=client, tenant=tenant)

    sub_type = request.data.get('type', 'limited')
    name     = request.data.get('name', '').strip()
    price    = request.data.get('price')

    if not name or not price:
        return Response({'error': 'name e price são obrigatórios.'}, status=400)

    visits_per_month = None
    if sub_type == 'limited':
        visits_per_month = request.data.get('visits_per_month')
        if not visits_per_month:
            return Response({'error': 'visits_per_month obrigatório para tipo limited.'}, status=400)
        visits_per_month = int(visits_per_month)

    from datetime import date as date_type
    active_from  = request.data.get('active_from', date_type.today().isoformat())
    active_until = request.data.get('active_until')

    sub = ClientSubscription.objects.create(
        tenant           = tenant,
        client           = client,
        name             = name,
        type             = sub_type,
        visits_per_month = visits_per_month,
        price            = float(price),
        active_from      = active_from,
        active_until     = active_until or None,
        notes            = request.data.get('notes', ''),
    )

    return Response({
        'id':               str(sub.id),
        'client':           {'name': client.name, 'phone': client.phone},
        'name':             sub.name,
        'type':             sub.type,
        'visits_per_month': sub.visits_per_month,
        'price':            float(sub.price),
        'active_from':      str(sub.active_from),
        'active_until':     str(sub.active_until) if sub.active_until else None,
    }, status=201)



@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def subscription_detail_view(request, subscription_id):
    """
    GET    /api/crm/subscriptions/{id}/ → detalhes
    PATCH  /api/crm/subscriptions/{id}/ → atualiza (renovar, pausar, cancelar)
    DELETE /api/crm/subscriptions/{id}/ → cancela
    """
    tenant = request.tenant

    try:
        sub = ClientSubscription.objects.select_related('client').get(
            id=subscription_id, tenant=tenant
        )
    except ClientSubscription.DoesNotExist:
        return Response({'error': 'Assinatura não encontrada.'}, status=404)

    if request.method == 'GET':
        return Response({
            'id':               str(sub.id),
            'client':           {'id': str(sub.client.id), 'name': sub.client.name, 'phone': sub.client.phone},
            'name':             sub.name,
            'type':             sub.type,
            'visits_per_month': sub.visits_per_month,
            'visits_used':      sub.visits_used,
            'visits_remaining': sub.visits_remaining,
            'price':            float(sub.price),
            'status':           sub.status,
            'active_from':      str(sub.active_from),
            'active_until':     str(sub.active_until) if sub.active_until else None,
            'can_visit':        sub.can_visit,
            'notes':            sub.notes,
        })

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method == 'PATCH':
        allowed = ['name', 'price', 'visits_per_month', 'active_until', 'status', 'notes']
        for field in allowed:
            if field in request.data:
                setattr(sub, field, request.data[field])
        sub.save()
        return Response({'message': 'Assinatura atualizada.'})

    if request.method == 'DELETE':
        sub.status = ClientSubscription.Status.CANCELLED
        sub.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Assinatura cancelada.'})


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def subscription_renew_view(request, subscription_id):
    """
    POST /api/crm/subscriptions/{id}/renew/
    Renova assinatura manualmente por X meses.
    Body: {"months": 1, "active_until": "2026-07-22"}
    """
    tenant = request.tenant

    try:
        sub = ClientSubscription.objects.get(id=subscription_id, tenant=tenant)
    except ClientSubscription.DoesNotExist:
        return Response({'error': 'Assinatura não encontrada.'}, status=404)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    active_until = request.data.get('active_until')
    if active_until:
        sub.active_until = active_until
    elif sub.active_until:
        from datetime import date as date_type
        months = int(request.data.get('months', 1))
        # Adiciona meses
        year  = sub.active_until.year + (sub.active_until.month + months - 1) // 12
        month = (sub.active_until.month + months - 1) % 12 + 1
        sub.active_until = date_type(year, month, sub.active_until.day)

    sub.status     = ClientSubscription.Status.ACTIVE
    sub.visits_used = 0  # reseta visitas do mês
    sub.save(update_fields=['active_until', 'status', 'visits_used', 'updated_at'])

    return Response({
        'message':     'Assinatura renovada.',
        'active_until':     str(sub.active_until) if sub.active_until else None,
        'visits_used':  sub.visits_used,
                    'active_from':      str(sub.active_from),
            
    })


# ── Helper ────────────────────────────────────────────────────────────────────

def _is_birthday_in_range(birthdate, start, end):
    """Verifica se o aniversário cai no intervalo (ignora o ano)."""
    try:
        this_year = birthdate.replace(year=start.year)
        if start <= this_year <= end:
            return True
        # Virada de ano
        next_year = birthdate.replace(year=start.year + 1)
        return start <= next_year <= end
    except ValueError:
        return False