# clients/models.py

import uuid
from django.db import models
from tenants.models import Tenant


class Client(models.Model):
    """
    Cliente da plataforma Beauti.
    Não pertence a um tenant — pertence à plataforma.
    """
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone      = models.CharField(max_length=20, unique=True)
    name       = models.CharField(max_length=100)
    email      = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class ClientTenantProfile(models.Model):
    """
    Histórico e fidelização do cliente por barbearia.
    Criado automaticamente no primeiro agendamento.
    """
    client         = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='tenant_profiles')
    tenant         = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='client_profiles')
    loyalty_points = models.PositiveIntegerField(default=0)
    last_visit_at  = models.DateTimeField(null=True, blank=True)
    total_visits   = models.PositiveIntegerField(default=0)
    notes          = models.TextField(blank=True, help_text="Observações do barbeiro sobre o cliente")
    birthdate      = models.DateField(null=True, blank=True, help_text="Data de aniversário")
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'client_tenant_profiles'
        unique_together = ('client', 'tenant')

    def __str__(self):
        return f"{self.client.name} @ {self.tenant.name}"

    @property
    def total_spent(self):
        from django.db.models import Sum
        return self.client.appointments.filter(
            tenant=self.tenant,
            status='completed'
        ).aggregate(total=Sum('price_snapshot'))['total'] or 0


class ClientOTP(models.Model):
    """Código de verificação enviado via WhatsApp. TTL: 10 minutos."""
    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    phone      = models.CharField(max_length=20)
    code       = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'client_otps'
        indexes  = [models.Index(fields=['tenant', 'phone', 'used'])]

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class ClientSubscription(models.Model):
    """
    Assinatura recorrente do cliente com a barbearia.
    Cobrança gerenciada fora do sistema por enquanto.

    Tipos:
    - unlimited: paga X/mês → visitas ilimitadas
    - limited:   paga X/mês → até visits_per_month visitas
    """

    class Type(models.TextChoices):
        UNLIMITED = 'unlimited', 'Ilimitado'
        LIMITED   = 'limited',   'Limitado (N visitas/mês)'

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Ativa'
        PAUSED    = 'paused',    'Pausada'
        CANCELLED = 'cancelled', 'Cancelada'
        EXPIRED   = 'expired',   'Expirada'

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant           = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='client_subscriptions')
    client           = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='subscriptions')
    name             = models.CharField(max_length=100, help_text="Ex: Assinatura Premium, Clube VIP")
    type             = models.CharField(max_length=20, choices=Type.choices, default=Type.LIMITED)
    visits_per_month = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Visitas permitidas por mês. Null = ilimitado."
    )
    price            = models.DecimalField(max_digits=8, decimal_places=2, help_text="Valor mensal")
    visits_used      = models.PositiveIntegerField(default=0, help_text="Visitas usadas no mês atual")
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    active_from      = models.DateField()
    active_until     = models.DateField(null=True, blank=True, help_text="Renovado manualmente")
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_subscriptions'
        ordering = ['-created_at']
        indexes  = [models.Index(fields=['tenant', 'status'])]

    def __str__(self):
        return f"{self.client.name} — {self.name} ({self.status})"

    @property
    def is_active(self):
        from django.utils import timezone
        if self.status != self.Status.ACTIVE:
            return False
        if self.active_until and timezone.now().date() > self.active_until:
            return False
        return True

    @property
    def visits_remaining(self):
        if self.type == self.Type.UNLIMITED:
            return None  # ilimitado
        if not self.visits_per_month:
            return None
        return max(0, self.visits_per_month - self.visits_used)

    @property
    def can_visit(self):
        if not self.is_active:
            return False
        if self.type == self.Type.UNLIMITED:
            return True
        return self.visits_remaining > 0

    def reset_monthly_visits(self):
        """Reseta visitas usadas no início do mês."""
        self.visits_used = 0
        self.save(update_fields=['visits_used', 'updated_at'])

    def use_visit(self):
        """Registra uma visita. Retorna True se bem-sucedido."""
        if not self.can_visit:
            return False
        if self.type == self.Type.LIMITED:
            self.visits_used += 1
            self.save(update_fields=['visits_used', 'updated_at'])
        return True