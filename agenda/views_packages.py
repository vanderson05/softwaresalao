# ════════════════════════════════════════════════════════════════
# agenda/views_packages.py
# Gestão de pacotes pelo owner no painel
# ════════════════════════════════════════════════════════════════
 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
 
from tenants.permissions import TenantAccessPermission, require_feature
from agenda.models import Package, ClientPackage, Service
from clients.models import Client
 
 
@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
@require_feature('packages')
def packages_view(request):
    """
    GET  /api/packages/  → lista pacotes do tenant
    POST /api/packages/  → cria pacote
    """
    tenant = request.tenant
 
    if request.method == 'GET':
        packages = Package.objects.filter(tenant=tenant).select_related('service')
        return Response([
            {
                'id':                str(p.id),
                'name':              p.name,
                'description':       p.description,
                'service':           {'id': str(p.service.id), 'name': p.service.name},
                'sessions':          p.sessions,
                'price':             float(p.price),
                'price_per_session': p.price_per_session,
                'original_price':    p.original_price,
                'discount_pct':      p.discount_pct,
                'is_active':         p.is_active,
            }
            for p in packages
        ])
 
    # POST
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)
 
    service_id = request.data.get('service_id')
    try:
        service = Service.objects.get(id=service_id, tenant=tenant, is_active=True)
    except Service.DoesNotExist:
        return Response({'error': 'Serviço não encontrado.'}, status=404)
 
    name     = request.data.get('name', '').strip()
    sessions = request.data.get('sessions')
    price    = request.data.get('price')
 
    if not name or not sessions or not price:
        return Response({'error': 'name, sessions e price são obrigatórios.'}, status=400)
 
    try:
        sessions = int(sessions)
        price    = float(price)
    except (ValueError, TypeError):
        return Response({'error': 'sessions deve ser inteiro e price decimal.'}, status=400)
 
    if sessions < 2:
        return Response({'error': 'Pacote deve ter pelo menos 2 sessões.'}, status=400)
 
    package = Package.objects.create(
        tenant      = tenant,
        name        = name,
        description = request.data.get('description', ''),
        service     = service,
        sessions    = sessions,
        price       = price,
    )
 
    return Response({
        'id':                str(package.id),
        'name':              package.name,
        'service':           package.service.name,
        'sessions':          package.sessions,
        'price':             float(package.price),
        'price_per_session': package.price_per_session,
        'discount_pct':      package.discount_pct,
    }, status=201)
 
 
@api_view(['POST'])
@permission_classes([TenantAccessPermission])
@require_feature('packages')
def assign_package_view(request):
    """
    POST /api/packages/assign/
    Barbeiro registra venda de pacote para cliente.
    Body: {"package_id": "uuid", "client_phone": "19999998888"}
    """
    tenant = request.tenant
 
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)
 
    package_id   = request.data.get('package_id')
    client_phone = ''.join(filter(str.isdigit, request.data.get('client_phone', '')))
 
    try:
        package = Package.objects.get(id=package_id, tenant=tenant, is_active=True)
    except Package.DoesNotExist:
        return Response({'error': 'Pacote não encontrado.'}, status=404)
 
    try:
        client = Client.objects.get(phone=client_phone)
    except Client.DoesNotExist:
        # Cria cliente automaticamente
        name   = request.data.get('client_name', '').strip()
        client = Client.objects.create(phone=client_phone, name=name or client_phone)
 
    from clients.models import ClientTenantProfile
    ClientTenantProfile.objects.get_or_create(client=client, tenant=tenant)
 
    client_package = ClientPackage.objects.create(
        tenant         = tenant,
        client         = client,
        package        = package,
        sessions_total = package.sessions,
    )
 
    return Response({
        'message':            f"Pacote '{package.name}' atribuído para {client.name or client.phone}.",
        'client_package_id':  str(client_package.id),
        'sessions_remaining': client_package.sessions_remaining,
    }, status=201)
 
 
@api_view(['GET'])
@permission_classes([TenantAccessPermission])
@require_feature('packages')
def client_packages_view(request):
    """
    GET /api/packages/clients/
    Lista pacotes ativos dos clientes do tenant.
    """
    tenant = request.tenant
 
    client_packages = ClientPackage.objects.filter(
        tenant=tenant,
        status=ClientPackage.Status.ACTIVE,
    ).select_related('client', 'package').order_by('-purchased_at')
 
    return Response([
        {
            'id':                 str(cp.id),
            'client':             {'name': cp.client.name, 'phone': cp.client.phone},
            'package':            cp.package.name,
            'service':            cp.package.service.name,
            'sessions_total':     cp.sessions_total,
            'sessions_used':      cp.sessions_used,
            'sessions_remaining': cp.sessions_remaining,
            'purchased_at':       cp.purchased_at.isoformat(),
            'is_available':       cp.is_available,
        }
        for cp in client_packages
    ])