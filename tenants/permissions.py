# tenants/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from tenants.models import TenantUser, PLAN_MAX_PROFESSIONALS, has_feature


# ── Acesso geral ao painel ────────────────────────────────────────────────────

class TenantAccessPermission(BasePermission):
    """
    Bloqueia acesso se:
    - Usuário não autenticado
    - Sem tenant vinculado
    - Tenant inativo
    - Trial expirado

    Injeta no request:
        request.tenant      → objeto Tenant
        request.tenant_user → objeto TenantUser
        request.tenant_role → string 'owner' | 'manager' | 'professional'
    """
    message = 'Seu período de acesso expirou. Escolha um plano para continuar.'
    ROLE_PERMISSIONS = {
    'owner': {
        'can_manage_team':    True,
        'can_view_financial': True,
        'can_manage_agenda':  True,   # todos os profissionais
        'can_view_crm':       True,
        'can_manage_config':  True,
    },
    'manager': {
        'can_manage_team':    False,
        'can_view_financial': True,
        'can_manage_agenda':  True,
        'can_view_crm':       True,
        'can_manage_config':  False,
    },
    'receptionist': {
        'can_manage_team':    False,
        'can_view_financial': False,
        'can_manage_agenda':  True,   # todos os profissionais
        'can_view_crm':       True,   # básico, sem financeiro
        'can_manage_config':  False,
    },
    'professional': {
        'can_manage_team':    False,
        'can_view_financial': False,
        'can_manage_agenda':  False,  # só própria agenda
        'can_view_crm':       False,
        'can_manage_config':  False,
    },
}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant_user = TenantUser.objects.filter(
            user=request.user, is_active=True
        ).select_related('tenant').first()

        if not tenant_user:
            return False

        tenant = tenant_user.tenant

        # Injeta no request para as views usarem sem nova query
        request.tenant      = tenant
        request.tenant_user = tenant_user
        request.tenant_role = tenant_user.role

        if not tenant.can_access:
            raise PermissionDenied({
                'error':       'trial_expired',
                'message':     self.message,
                'upgrade_url': '/planos',
            })

        return True


# ── Roles ─────────────────────────────────────────────────────────────────────

class IsOwnerOrManager(BasePermission):
    """Permite apenas owner e manager."""
    message = 'Apenas donos e gerentes podem realizar esta ação.'

    def has_permission(self, request, view):
        return getattr(request, 'tenant_role', None) in ('owner', 'manager')


class IsOwner(BasePermission):
    """Permite apenas o dono do estabelecimento."""
    message = 'Apenas o dono pode realizar esta ação.'

    def has_permission(self, request, view):
        return getattr(request, 'tenant_role', None) == 'owner'


# ── Verificação de feature ────────────────────────────────────────────────────

def check_feature(tenant, feature_name: str, friendly_name: str = None):
    """
    Verifica se o tenant tem acesso a uma feature.
    Lança PermissionDenied se não tiver.

    Uso:
        check_feature(request.tenant, 'financial', 'Gestão financeira')
    """
    if not has_feature(tenant, feature_name):
        name = friendly_name or feature_name
        raise PermissionDenied({
            'error':       'feature_not_available',
            'message':     f'{name} não está disponível no plano {tenant.plan.title()}.',
            'feature':     feature_name,
            'plan':        tenant.plan,
            'upgrade_url': '/planos',
        })


# ── Mapa de features com nome amigável ───────────────────────────────────────
# Usado para gerar mensagens de erro legíveis

FEATURE_NAMES = {
    'agent_whatsapp':  'Agente WhatsApp com IA',
    'reminders':       'Lembretes automáticos',
    'agenda':          'Agenda online',
    'waiting_list':    'Lista de espera',
    'services':        'Cadastro de serviços',
    'packages':        'Pacotes de serviços',
    'client_history':  'Histórico de clientes',
    'return_messages': 'Mensagens de retorno',
    'birthday_message':'Parabéns de aniversário',
    'loyalty_points':  'Programa de pontos',
    'nps':             'Pesquisa de satisfação (NPS)',
    'promo_blast':     'Envio de promoções',
    'financial':       'Gestão financeira',
    'commissions':     'Comissões',
    'reports':         'Relatórios',
    'ai_insights':     'Insights de IA',
    'custom_domain':   'Domínio customizado',
    'dedicated_support': 'Suporte dedicado',
}


def require_feature(feature_name: str):
    """
    Decorator para views que exigem uma feature específica.
    Deve ser usado APÓS TenantAccessPermission estar no permission_classes.

    Uso:
        @api_view(['GET'])
        @permission_classes([TenantAccessPermission])
        @require_feature('financial')
        def cashbox_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                raise PermissionDenied('Tenant não identificado.')

            friendly = FEATURE_NAMES.get(feature_name, feature_name)
            check_feature(tenant, feature_name, friendly)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ── Limite de profissionais ───────────────────────────────────────────────────

def check_professional_limit(tenant):
    """
    Verifica se o tenant pode adicionar mais profissionais.
    Lança PermissionDenied se atingiu o limite do plano.

    Uso:
        check_professional_limit(request.tenant)
    """
    from agenda.models import Professional

    current = Professional.objects.filter(
        tenant=tenant, is_active=True
    ).count()

    limit = PLAN_MAX_PROFESSIONALS.get(tenant.plan, 1)

    if current >= limit:
        raise PermissionDenied({
            'error':       'professional_limit_reached',
            'message':     (
                f"Seu plano {tenant.plan.title()} permite até {limit} "
                f"profissional(is) ativo(s). "
                f"Faça upgrade para adicionar mais."
            ),
            'current':     current,
            'limit':       limit,
            'upgrade_url': '/planos',
        })


# ── Verificação de downgrade ──────────────────────────────────────────────────

def check_downgrade(tenant, new_plan: str):
    """
    Verifica se o tenant pode fazer downgrade para o novo plano.
    Lança PermissionDenied se tiver profissionais além do limite.

    Uso:
        check_downgrade(request.tenant, 'starter')
    """
    pode, erro = tenant.can_downgrade_to(new_plan)
    if not pode:
        raise PermissionDenied({
            'error':       'downgrade_blocked',
            'message':     erro,
            'upgrade_url': '/profissionais',
        })