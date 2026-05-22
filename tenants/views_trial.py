# tenants/views_trial.py
# Views relacionadas ao trial — adicionar ao tenants/views.py

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenants.models import TenantUser, PLAN_MAX_PROFESSIONALS, PLAN_MONTHLY_PRICE


# ── GET /api/trial/status/ ───────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trial_status_view(request):
    """
    Retorna o status atual do trial do tenant autenticado.
    Usado pelo frontend para exibir banner de aviso.
    """
    tenant_user = TenantUser.objects.filter(
        user=request.user, is_active=True
    ).select_related('tenant').first()

    if not tenant_user:
        return Response({'error': 'Tenant não encontrado.'}, status=404)

    tenant = tenant_user.tenant

    return Response({
        'plan':               tenant.plan,
        'is_active':          tenant.is_active,
        'is_trial':           tenant.plan == 'trial',
        'is_trial_active':    tenant.is_trial_active,
        'is_trial_expired':   tenant.is_trial_expired,
        'trial_ends_at':      tenant.trial_ends_at,
        'trial_days_remaining': tenant.trial_days_remaining,
        'can_access':         tenant.can_access,
        'max_professionals':  tenant.max_professionals,
    })


# ── GET /api/plans/ ──────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def plans_view(request):
    """
    Lista os planos disponíveis para upgrade.
    """
    plans = [
        {
            'id':               'starter',
            'name':             'Starter',
            'description':      '1 Profissional',
            'price_monthly':    PLAN_MONTHLY_PRICE['starter'],
            'price_annual':     round(PLAN_MONTHLY_PRICE['starter'] * 12 * 0.70, 2),
            'max_professionals': PLAN_MAX_PROFESSIONALS['starter'],
            'features': [
                'Agente WhatsApp com IA',
                'Agenda online',
                'Lembretes automáticos',
                'Cadastro de clientes',
                'Suporte via e-mail',
            ],
        },
        {
            'id':               'pro',
            'name':             'Pro',
            'description':      '2 a 5 Profissionais',
            'price_monthly':    PLAN_MONTHLY_PRICE['pro'],
            'price_annual':     round(PLAN_MONTHLY_PRICE['pro'] * 12 * 0.70, 2),
            'max_professionals': PLAN_MAX_PROFESSIONALS['pro'],
            'recommended':      True,
            'features': [
                'Tudo do Starter',
                'Até 5 profissionais',
                'Gestão financeira',
                'Comissões automáticas',
                'Fidelização de clientes',
                'NPS automático',
                'Mensagens de retorno',
            ],
        },
        {
            'id':               'advanced',
            'name':             'Advanced',
            'description':      '6 a 15 Profissionais',
            'price_monthly':    PLAN_MONTHLY_PRICE['advanced'],
            'price_annual':     round(PLAN_MONTHLY_PRICE['advanced'] * 12 * 0.70, 2),
            'max_professionals': PLAN_MAX_PROFESSIONALS['advanced'],
            'features': [
                'Tudo do Pro',
                'Até 15 profissionais',
                'Insights de IA',
                'Suporte a áudio no WhatsApp',
                'Domínio customizado',
                'Envio de promoções',
            ],
        },
        {
            'id':               'enterprise',
            'name':             'Enterprise',
            'description':      '+15 Profissionais',
            'price_monthly':    PLAN_MONTHLY_PRICE['enterprise'],
            'price_annual':     round(PLAN_MONTHLY_PRICE['enterprise'] * 12 * 0.70, 2),
            'max_professionals': PLAN_MAX_PROFESSIONALS['enterprise'],
            'features': [
                'Tudo do Advanced',
                'Profissionais ilimitados',
                'Suporte prioritário',
                'Onboarding dedicado',
                'SLA garantido',
            ],
        },
    ]

    return Response({'plans': plans})