# tenants/models.py

import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


# ── Planos ────────────────────────────────────────────────────────────────────

class Plan(models.TextChoices):
    TRIAL      = 'trial',      'Trial 14 dias'
    STARTER    = 'starter',    'Starter — 1 Profissional'
    PRO        = 'pro',        'Pro — 2 a 5 Profissionais'
    ADVANCED   = 'advanced',   'Advanced — 6 a 15 Profissionais'
    ENTERPRISE = 'enterprise', 'Enterprise — +15 Profissionais'


# ── Limite de profissionais por plano ─────────────────────────────────────────

PLAN_MAX_PROFESSIONALS = {
    'trial':      999,
    'starter':    1,
    'pro':        5,
    'advanced':   15,
    'enterprise': 999,
}


# ── Preços mensais ────────────────────────────────────────────────────────────

PLAN_MONTHLY_PRICE = {
    'trial':      0,
    'starter':    99.90,
    'pro':        149.90,
    'advanced':   199.90,
    'enterprise': 279.90,
}


# ── Features por plano — fonte única de verdade ───────────────────────────────
# Removidos: audio_support, multi_language (complexidade sem retorno agora)

PLAN_FEATURES = {
    'trial': [
        # M1 — Agente
        'agent_whatsapp',
        'reminders',
        # M2 — Agenda
        'agenda',
        'waiting_list',
        # M3 — Gestão
        'services',
        'packages',
        # M4 — CRM
        'client_history',
        'return_messages',
        'birthday_message',
        'loyalty_points',
        'nps',
        'promo_blast',
        # M5 — Financeiro
        'financial',
        'commissions',
        'reports',
        'ai_insights',
        # M6 — Plataforma
        'custom_domain',
    ],

    'starter': [
        # M1 — Agente
        'agent_whatsapp',
        'reminders',
        # M2 — Agenda
        'agenda',
        # M3 — Gestão
        'services',
        # M4 — CRM (só histórico)
        'client_history',
        # SEM: waiting_list, packages, return_messages,
        #      birthday_message, loyalty_points, nps,
        #      promo_blast, financial, commissions,
        #      reports, ai_insights, custom_domain
    ],

    'pro': [
        # M1 — Agente
        'agent_whatsapp',
        'reminders',
        # M2 — Agenda
        'agenda',
        'waiting_list',
        # M3 — Gestão
        'services',
        'packages',
        # M4 — CRM
        'client_history',
        'return_messages',
        'birthday_message',
        'loyalty_points',
        'nps',
        # M5 — Financeiro
        'financial',
        'commissions',
        'reports',
        # SEM: promo_blast, ai_insights, custom_domain
    ],

    'advanced': [
        # M1 — Agente
        'agent_whatsapp',
        'reminders',
        # M2 — Agenda
        'agenda',
        'waiting_list',
        # M3 — Gestão
        'services',
        'packages',
        'custom_domain',
        # M4 — CRM
        'client_history',
        'return_messages',
        'birthday_message',
        'loyalty_points',
        'nps',
        'promo_blast',
        # M5 — Financeiro
        'financial',
        'commissions',
        'reports',
        'ai_insights',
    ],

    'enterprise': [
        # Tudo do Advanced +
        'agent_whatsapp',
        'reminders',
        'agenda',
        'waiting_list',
        'services',
        'packages',
        'custom_domain',
        'client_history',
        'return_messages',
        'birthday_message',
        'loyalty_points',
        'nps',
        'promo_blast',
        'financial',
        'commissions',
        'reports',
        'ai_insights',
        # Exclusivo Enterprise
        'dedicated_support',
    ],
}


def has_feature(tenant, feature_name: str) -> bool:
    """
    Verifica se o tenant tem acesso a uma feature.

    Uso:
        if not has_feature(request.tenant, 'financial'):
            return Response({'error': 'feature_not_available'}, status=403)
    """
    return feature_name in PLAN_FEATURES.get(tenant.plan, [])


def get_plan_features(plan: str) -> list:
    """Retorna lista de features de um plano."""
    return PLAN_FEATURES.get(plan, [])


# ── Tenant ────────────────────────────────────────────────────────────────────

class Tenant(models.Model):

    class EstablishmentType(models.TextChoices):
        BARBERSHOP = 'barbershop', 'Barbearia'
        SALON      = 'salon',      'Salão de Beleza'
        STUDIO     = 'studio',     'Studio'

    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)

    # Dados básicos
    name     = models.CharField(max_length=120)
    type     = models.CharField(max_length=20, choices=EstablishmentType.choices, default=EstablishmentType.BARBERSHOP)
    phone    = models.CharField(max_length=20, blank=True)
    email    = models.EmailField(blank=True)
    address  = models.CharField(max_length=255, blank=True)
    city     = models.CharField(max_length=100, blank=True)
    logo_url = models.URLField(blank=True)

    # Plano e status
    plan      = models.CharField(max_length=20, choices=Plan.choices, default=Plan.TRIAL)
    is_active = models.BooleanField(default=True)

    # Trial
    trial_ends_at = models.DateTimeField(null=True, blank=True)

    # Onboarding
    email_verified  = models.BooleanField(default=False)
    setup_completed = models.BooleanField(default=False)

    # WhatsApp
    wa_phone_number_id = models.CharField(max_length=50, blank=True)
    wa_token           = models.TextField(blank=True)
    wa_verify_token    = models.CharField(max_length=100, blank=True)

    # Domínio customizado (Advanced+)
    custom_domain = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table         = 'tenants'
        verbose_name     = 'Estabelecimento'
        verbose_name_plural = 'Estabelecimentos'

    def __str__(self):
        return f"{self.name} [{self.plan}]"

    # ── Propriedades ──────────────────────────────────────────────────────────

    @property
    def is_trial_active(self):
        if self.plan != Plan.TRIAL:
            return False
        if not self.trial_ends_at:
            return False
        return timezone.now() < self.trial_ends_at

    @property
    def is_trial_expired(self):
        return self.plan == Plan.TRIAL and not self.is_trial_active

    @property
    def trial_days_remaining(self):
        if not self.trial_ends_at or self.plan != Plan.TRIAL:
            return 0
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)

    @property
    def max_professionals(self):
        return PLAN_MAX_PROFESSIONALS.get(self.plan, 1)

    @property
    def can_access(self):
        if not self.is_active:
            return False
        if self.plan == Plan.TRIAL:
            return self.is_trial_active
        return True

    @property
    def features(self):
        """Retorna lista de features ativas do tenant."""
        return PLAN_FEATURES.get(self.plan, [])

    def has_feature(self, feature_name: str) -> bool:
        """Atalho para verificar feature diretamente no tenant."""
        return has_feature(self, feature_name)

    # ── Métodos de negócio ────────────────────────────────────────────────────

    def activate_plan_features(self):
        """
        Chamado após upgrade/downgrade via Stripe webhook.
        Não precisa mais alterar campos individuais —
        as features são derivadas do plan via PLAN_FEATURES.
        Só salva o plano e limpa custom_domain se necessário.
        """
        # Remove custom_domain se plano não suporta
        if not self.has_feature('custom_domain') and self.custom_domain:
            self.custom_domain = ''

        self.save(update_fields=['plan', 'custom_domain', 'updated_at'])

    def can_downgrade_to(self, new_plan: str) -> tuple[bool, str]:
        """
        Verifica se o tenant pode fazer downgrade para o novo plano.
        Retorna (pode_fazer, mensagem_de_erro).

        Uso:
            pode, erro = tenant.can_downgrade_to('starter')
            if not pode:
                return Response({'error': erro}, status=400)
        """
        from django.db.models import Q

        new_limit = PLAN_MAX_PROFESSIONALS.get(new_plan, 1)

        # Conta profissionais ativos (import local para evitar circular)
        try:
            from agenda.models import Professional
            current = Professional.objects.filter(
                tenant=self, is_active=True
            ).count()
        except Exception:
            current = 0

        if current > new_limit:
            excesso = current - new_limit
            return False, (
                f"Você tem {current} profissional(is) ativo(s). "
                f"O plano {new_plan.title()} permite apenas {new_limit}. "
                f"Desative {excesso} profissional(is) antes de fazer o downgrade."
            )

        return True, ""

    @classmethod
    def generate_unique_slug(cls, name: str) -> str:
        from django.utils.text import slugify
        base_slug = slugify(name)
        slug      = base_slug
        counter   = 2
        while cls.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug


# ── TenantUser ────────────────────────────────────────────────────────────────

class TenantUser(models.Model):

    class Role(models.TextChoices):
        OWNER        = 'owner',        'Dono'
        MANAGER      = 'manager',      'Gerente'
        PROFESSIONAL = 'professional', 'Profissional'

    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='tenant_users')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_users')
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table       = 'tenant_users'
        unique_together = ('tenant', 'user')
        verbose_name   = 'Usuário do estabelecimento'
        verbose_name_plural = 'Usuários dos estabelecimentos'

    def __str__(self):
        return f"{self.user.email} → {self.tenant.name} [{self.role}]"


# ── EmailVerification ─────────────────────────────────────────────────────────

class EmailVerification(models.Model):

    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token       = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at  = models.DateTimeField()
    verified    = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'email_verifications'
        verbose_name = 'Verificação de e-mail'

    def __str__(self):
        return f"{self.user.email} — {'verificado' if self.verified else 'pendente'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)


# ── TenantBusinessHours ───────────────────────────────────────────────────────

class TenantBusinessHours(models.Model):

    WEEKDAYS = [
        (0, 'Segunda-feira'), (1, 'Terça-feira'),  (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),  (4, 'Sexta-feira'),  (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='business_hours')
    weekday    = models.IntegerField(choices=WEEKDAYS)
    open_time  = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed  = models.BooleanField(default=False)

    class Meta:
        db_table        = 'tenant_business_hours'
        unique_together = ('tenant', 'weekday')
        ordering        = ['weekday']
        verbose_name    = 'Horário de funcionamento'
        verbose_name_plural = 'Horários de funcionamento'

    def __str__(self):
        if self.is_closed:
            return f"{self.get_weekday_display()} — Fechado"
        return f"{self.get_weekday_display()} {self.open_time}–{self.close_time}"