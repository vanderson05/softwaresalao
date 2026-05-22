# apps/tenants/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    EmailVerifySerializer,
    ResendVerificationSerializer,
    TenantBasicSerializer,
)
from .models import TenantUser
from .emails import (
    send_welcome_email,
    send_resend_verification_email,
)


# ── POST /api/auth/register/ ─────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Cadastro de novo estabelecimento.
    Cria User + Tenant + TenantUser + EmailVerification + AgentConfig.
    """
    serializer = RegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user, tenant = serializer.save()

    # Envia e-mail de boas-vindas + verificação
    try:
        verification = user.email_verification
        send_welcome_email(user, tenant, verification.token)
    except Exception as e:
        # Não bloqueia o cadastro se e-mail falhar
        print(f"[EMAIL ERROR] {e}")

    return Response({
        'message': 'Cadastro realizado com sucesso! Verifique seu e-mail para ativar o acesso.',
        'tenant': {
            'slug':           tenant.slug,
            'name':           tenant.name,
            'plan':           tenant.plan,
            'trial_ends_at':  tenant.trial_ends_at,
            'trial_days_remaining': tenant.trial_days_remaining,
        }
    }, status=status.HTTP_201_CREATED)


# ── POST /api/auth/login/ ────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login com e-mail e senha.
    Retorna JWT com claims do tenant.
    """
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user        = serializer.validated_data['user']
    tenant      = serializer.validated_data['tenant']
    tenant_user = serializer.validated_data['tenant_user']

    tokens = serializer.get_tokens(user, tenant, tenant_user)

    return Response({
        'tokens': tokens,
        'user': {
            'id':    user.id,
            'email': user.email,
            'name':  f"{user.first_name} {user.last_name}".strip() or user.email,
        },
        'tenant': TenantBasicSerializer(tenant).data,
        'role':   tenant_user.role,
    }, status=status.HTTP_200_OK)


# ── GET /api/auth/verify/?token=xxx ─────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email_view(request):
    """
    Verifica token de confirmação de e-mail.
    """
    token = request.query_params.get('token')

    if not token:
        return Response(
            {'error': 'Token não informado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = EmailVerifySerializer(data={'token': token})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()

    return Response({
        'message': 'E-mail verificado com sucesso! Você já pode acessar o painel.',
        'email': user.email,
    }, status=status.HTTP_200_OK)


# ── POST /api/auth/resend-verification/ ─────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_view(request):
    """
    Reenvia e-mail de verificação.
    """
    serializer = ResendVerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    verification = serializer.save()

    if verification:
        try:
            send_resend_verification_email(verification.user, verification.token)
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")

    # Sempre retorna a mesma mensagem (não revela se e-mail existe)
    return Response({
        'message': 'Se este e-mail estiver cadastrado, você receberá um novo link em instantes.'
    }, status=status.HTTP_200_OK)


# ── GET /api/auth/me/ ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Retorna dados do usuário e tenant autenticado.
    Usado pelo frontend para checar sessão ativa.
    """
    tenant_user = TenantUser.objects.filter(
        user=request.user, is_active=True
    ).select_related('tenant').first()

    if not tenant_user:
        return Response(
            {'error': 'Nenhum estabelecimento encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    tenant = tenant_user.tenant

    return Response({
        'user': {
            'id':    request.user.id,
            'email': request.user.email,
            'name':  f"{request.user.first_name} {request.user.last_name}".strip(),
        },
        'tenant':       TenantBasicSerializer(tenant).data,
        'role':         tenant_user.role,
        'can_access':   tenant.can_access,
        'trial_expired': tenant.is_trial_expired,
    }, status=status.HTTP_200_OK)