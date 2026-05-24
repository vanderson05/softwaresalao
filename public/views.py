# public/views.py
# Endpoints públicos — perfil da barbearia, auth cliente final, agendamento
 
import random
import logging
from datetime import datetime, timedelta, date as date_type
 
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
 
from tenants.models import Tenant
from clients.models import Client, ClientTenantProfile, ClientOTP
from agenda.models import Professional, Service, Appointment, Package
 
logger = logging.getLogger(__name__)
 
 
# ── Helpers ───────────────────────────────────────────────────────────────────
 
def _get_tenant(slug):
    try:
        return Tenant.objects.get(slug=slug, is_active=True, setup_completed=True)
    except Tenant.DoesNotExist:
        return None
 
 
def _get_client_from_token(request):
    """Extrai client do JWT do cliente final."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('ClientBearer '):
        return None
    token = auth.replace('ClientBearer ', '')
    try:
        import jwt as pyjwt
        from django.conf import settings
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload.get('token_type') != 'client_access':
            return None
        return Client.objects.get(id=payload['client_id'])
    except Exception:
        return None
 
 
def _generate_client_token(client, tenant):
    """Gera JWT para o cliente final."""
    import jwt as pyjwt
    from django.conf import settings
    payload = {
        'token_type':  'client_access',
        'client_id':   str(client.id),
        'tenant_id':   str(tenant.id),
        'tenant_slug': tenant.slug,
        'phone':       client.phone,
        'exp':         datetime.utcnow() + timedelta(days=30),
    }
    return pyjwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

# ════════════════════════════════════════════════════════════════
# HOME PÚBLICA — lista barbearias
# ════════════════════════════════════════════════════════════════
 
@api_view(['GET'])
@permission_classes([AllowAny])
def home_view(request):
    """
    GET /b/
    Lista barbearias da plataforma.
    Filtros: ?q=nome&city=americana
    """
    qs = Tenant.objects.filter(is_active=True, setup_completed=True)
 
    q    = request.query_params.get('q', '').strip()
    city = request.query_params.get('city', '').strip()
 
    if q:
        qs = qs.filter(name__icontains=q)
    if city:
        qs = qs.filter(city__icontains=city)
 
    qs = qs.order_by('name')[:50]
 
    result = []
    for t in qs:
        services_count = t.services.filter(is_active=True).count()
        result.append({
            'slug':           t.slug,
            'name':           t.name,
            'type':           t.get_type_display(),
            'city':           t.city,
            'address':        t.address,
            'logo_url':       t.logo_url,
            'services_count': services_count,
            'url':            f"/b/{t.slug}/",
        })
 
    return Response({
        'results': result,
        'total':   len(result),
    })
 
 
# ════════════════════════════════════════════════════════════════
# PERFIL DA BARBEARIA — público
# ════════════════════════════════════════════════════════════════
 
@api_view(['GET'])
@permission_classes([AllowAny])
def profile_view(request, slug):
    """
    GET /b/{slug}/
    Perfil público da barbearia.
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    hours = tenant.business_hours.order_by('weekday')
    days  = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
 
    return Response({
        'slug':     tenant.slug,
        'name':     tenant.name,
        'type':     tenant.get_type_display(),
        'address':  tenant.address,
        'city':     tenant.city,
        'phone':    tenant.phone,
        'logo_url': tenant.logo_url,
        'business_hours': [
            {
                'weekday':         h.weekday,
                'weekday_display': days[h.weekday],
                'open_time':       h.open_time.strftime('%H:%M') if h.open_time else None,
                'close_time':      h.close_time.strftime('%H:%M') if h.close_time else None,
                'is_closed':       h.is_closed,
            }
            for h in hours
        ],
        'wa_available': tenant.agent_config.is_whatsapp_connected if hasattr(tenant, 'agent_config') else False,
    })
 
 
@api_view(['GET'])
@permission_classes([AllowAny])
def public_services_view(request, slug):
    """GET /b/{slug}/services/ — serviços e preços"""
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    services = Service.objects.filter(tenant=tenant, is_active=True)
    return Response([
        {
            'id':           str(s.id),
            'name':         s.name,
            'description':  s.description,
            'duration_min': s.duration_min,
            'price':        float(s.price),
        }
        for s in services
    ])
 
 
@api_view(['GET'])
@permission_classes([AllowAny])
def public_professionals_view(request, slug):
    """GET /b/{slug}/professionals/ — profissionais ativos"""
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    return Response([
        {
            'id':       str(p.id),
            'name':     p.name,
            'photo_url': p.photo_url,
            'bio':      p.bio,
        }
        for p in professionals
    ])
 
 
@api_view(['GET'])
@permission_classes([AllowAny])
def public_packages_view(request, slug):
    """GET /b/{slug}/packages/ — pacotes disponíveis"""
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    packages = Package.objects.filter(tenant=tenant, is_active=True).select_related('service')
    return Response([
        {
            'id':                str(p.id),
            'name':              p.name,
            'description':       p.description,
            'service_name':      p.service.name,
            'sessions':          p.sessions,
            'price':             float(p.price),
            'price_per_session': p.price_per_session,
            'original_price':    p.original_price,
            'discount_pct':      p.discount_pct,
        }
        for p in packages
    ])
 
 
# ════════════════════════════════════════════════════════════════
# AUTH DO CLIENTE FINAL — código via WhatsApp
# ════════════════════════════════════════════════════════════════
 
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_request_code_view(request, slug):
    """
    POST /b/{slug}/auth/request-code/
    Envia código de 6 dígitos via WhatsApp.
    Body: {"phone": "19999998888"}
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    phone = request.data.get('phone', '').strip()
    phone = ''.join(filter(str.isdigit, phone))
 
    if len(phone) < 10 or len(phone) > 11:
        return Response({'error': 'Telefone inválido. Use DDD + número.'}, status=400)
 
    # Invalida OTPs anteriores
    ClientOTP.objects.filter(tenant=tenant, phone=phone, used=False).update(used=True)
 
    # Gera novo código
    code       = str(random.randint(100000, 999999))
    expires_at = timezone.now() + timedelta(minutes=10)
 
    ClientOTP.objects.create(
        tenant=tenant,
        phone=phone,
        code=code,
        expires_at=expires_at,
    )
 
    # Envia via WhatsApp
    message = (
        f"Seu código de acesso à {tenant.name}: *{code}*\n"
        f"Válido por 10 minutos. Não compartilhe com ninguém."
    )
 
    try:
        if hasattr(tenant, 'agent_config') and tenant.agent_config.is_whatsapp_connected:
            from agent.whatsapp import send_message
            send_message(
                tenant.agent_config.wa_phone_number_id,
                tenant.agent_config.wa_token,
                phone,
                message,
            )
            logger.info(f"[OTP] Código enviado para {phone} via WhatsApp")
        else:
            # Desenvolvimento — imprime no console
            logger.info(f"[OTP DEV] {phone} → {code}")
            print(f"\n[OTP DEV] Telefone: {phone} | Código: {code}\n")
    except Exception as e:
        logger.error(f"[OTP ERROR] {e}")
 
    return Response({
        'message': 'Código enviado via WhatsApp.',
        'phone':   phone,
        'expires_in_minutes': 10,
    })
 
 
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_verify_code_view(request, slug):
    """
    POST /b/{slug}/auth/verify-code/
    Valida código → retorna JWT do cliente.
    Body: {"phone": "19999998888", "code": "847291"}
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    phone = ''.join(filter(str.isdigit, request.data.get('phone', '')))
    code  = request.data.get('code', '').strip()
 
    if not phone or not code:
        return Response({'error': 'phone e code são obrigatórios.'}, status=400)
 
    # Busca OTP válido
    otp = ClientOTP.objects.filter(
        tenant=tenant,
        phone=phone,
        code=code,
        used=False,
    ).first()
 
    if not otp:
        return Response({'error': 'Código inválido.'}, status=400)
 
    if otp.is_expired:
        return Response({'error': 'Código expirado. Solicite um novo.'}, status=400)
 
    # Marca como usado
    otp.used = True
    otp.save(update_fields=['used'])
 
    # Cria ou busca cliente na plataforma
    client, is_new = Client.objects.get_or_create(
        phone=phone,
        defaults={'name': ''}
    )
 
    # Cria perfil no tenant se não existe
    ClientTenantProfile.objects.get_or_create(
        client=client,
        tenant=tenant,
    )
 
    # Gera JWT do cliente
    token = _generate_client_token(client, tenant)
 
    return Response({
        'token':        token,
        'is_new_client': is_new,
        'client': {
            'id':    str(client.id),
            'phone': client.phone,
            'name':  client.name,
        },
    })
 
 
# ════════════════════════════════════════════════════════════════
# ÁREA DO CLIENTE — requer JWT do cliente
# ════════════════════════════════════════════════════════════════
 
@api_view(['PATCH'])
@permission_classes([AllowAny])
def client_me_view(request, slug):
    """
    PATCH /b/{slug}/me/
    Atualiza nome do cliente (usado no primeiro acesso).
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    client = _get_client_from_token(request)
    if not client:
        return Response({'error': 'Não autenticado.'}, status=401)
 
    name = request.data.get('name', '').strip()
    if not name:
        return Response({'error': 'name obrigatório.'}, status=400)
 
    client.name = name
    client.save(update_fields=['name', 'updated_at'])
 
    return Response({
        'message': 'Nome atualizado.',
        'client':  {'id': str(client.id), 'name': client.name, 'phone': client.phone},
    })
 
 
@api_view(['GET'])
@permission_classes([AllowAny])
def public_slots_view(request, slug):
    """
    GET /b/{slug}/slots/?service_id=xxx&date=2026-05-26&professional_id=xxx
    Slots disponíveis — requer JWT do cliente.
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    client = _get_client_from_token(request)
    if not client:
        return Response({'error': 'Faça login para ver horários disponíveis.'}, status=401)
 
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
        return Response({'error': 'date inválido.'}, status=400)
 
    try:
        service = Service.objects.get(id=service_id, tenant=tenant, is_active=True)
    except Service.DoesNotExist:
        return Response({'error': 'Serviço não encontrado.'}, status=404)
 
    from agenda.slots import get_available_slots, get_next_available_slots
 
    if professional_id:
        try:
            professional = Professional.objects.get(id=professional_id, tenant=tenant, is_active=True)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado.'}, status=404)
 
        slots = get_available_slots(professional, service, query_date)
        return Response({
            'date':         date_str,
            'professional': {'id': str(professional.id), 'name': professional.name},
            'service':      {'id': str(service.id), 'name': service.name},
            'slots':        slots,
        })
 
    # Todos os profissionais
    slots = get_next_available_slots(tenant, service, days_ahead=7)
    return Response({
        'service': {'id': str(service.id), 'name': service.name},
        'slots':   slots,
    })
 
 
@api_view(['POST'])
@permission_classes([AllowAny])
def book_view(request, slug):
    """
    POST /b/{slug}/book/
    Cria agendamento com source=link.
    Requer JWT do cliente.
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    client = _get_client_from_token(request)
    if not client:
        return Response({'error': 'Faça login para agendar.'}, status=401)
 
    # Injeta dados do cliente
    data = request.data.copy()
    data['source']       = 'link'
    data['client_name']  = data.get('client_name', client.name)
    data['client_phone'] = client.phone
 
    from agenda.serializers_appointment import AppointmentCreateSerializer
 
    class FakeRequest:
        def __init__(self, tenant, role='owner'):
            self.tenant      = tenant
            self.tenant_role = role
 
    serializer = AppointmentCreateSerializer(
        data=data,
        context={'request': FakeRequest(tenant)}
    )
 
    if serializer.is_valid():
        appointment = serializer.save()
        return Response({
            'message': 'Agendamento realizado com sucesso!',
            'appointment': {
                'id':               str(appointment.id),
                'service':          appointment.service.name,
                'professional':     appointment.professional.name,
                'starts_at':        appointment.starts_at.isoformat(),
                'ends_at':          appointment.ends_at.isoformat(),
                'status':           appointment.status,
                'price':            float(appointment.price_snapshot or 0),
                'address':          f"{tenant.address}, {tenant.city}",
            }
        }, status=201)
 
    return Response(serializer.errors, status=400)
 
 
@api_view(['GET'])
@permission_classes([AllowAny])
def my_appointments_view(request, slug):
    """
    GET /b/{slug}/my-appointments/
    Agendamentos do cliente nesta barbearia.
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    client = _get_client_from_token(request)
    if not client:
        return Response({'error': 'Não autenticado.'}, status=401)
 
    appointments = Appointment.objects.filter(
        tenant=tenant,
        client=client,
    ).select_related('service', 'professional').order_by('-starts_at')
 
    upcoming = [a for a in appointments if a.starts_at > timezone.now() and a.status in ('pending', 'confirmed')]
    past     = [a for a in appointments if a not in upcoming]
 
    def serialize(a):
        return {
            'id':             str(a.id),
            'service':        a.service.name,
            'professional':   a.professional.name,
            'starts_at':      a.starts_at.isoformat(),
            'status':         a.status,
            'status_display': a.get_status_display(),
            'price':          float(a.price_snapshot or 0),
        }
 
    return Response({
        'upcoming': [serialize(a) for a in upcoming],
        'past':     [serialize(a) for a in past[:10]],
    })
 
 
@api_view(['POST'])
@permission_classes([AllowAny])
def my_appointment_cancel_view(request, slug, appointment_id):
    """
    POST /b/{slug}/my-appointments/{id}/cancel/
    Cliente cancela seu próprio agendamento.
    """
    tenant = _get_tenant(slug)
    if not tenant:
        return Response({'error': 'Barbearia não encontrada.'}, status=404)
 
    client = _get_client_from_token(request)
    if not client:
        return Response({'error': 'Não autenticado.'}, status=401)
 
    try:
        appointment = Appointment.objects.get(
            id=appointment_id, tenant=tenant, client=client
        )
    except Appointment.DoesNotExist:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)
 
    if appointment.status in ('completed', 'cancelled', 'no_show'):
        return Response({
            'error': f"Não é possível cancelar um agendamento com status '{appointment.get_status_display()}'."
        }, status=400)
 
    appointment.status = Appointment.Status.CANCELLED
    appointment.save(update_fields=['status', 'updated_at'])
 
    return Response({
        'message':  'Agendamento cancelado.',
        'status':   appointment.status,
    })