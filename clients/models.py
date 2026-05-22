# clients/models.py
import uuid
from django.db import models
from tenants.models import Tenant


class Client(models.Model):
    """
    Cliente da plataforma Beauti.
    Não pertence a um tenant — pertence à plataforma.
    Um cliente pode agendar em qualquer barbearia.
    """
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone     = models.CharField(max_length=20, unique=True)
    name      = models.CharField(max_length=100)
    email     = models.EmailField(blank=True)
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
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'client_tenant_profiles'
        unique_together = ('client', 'tenant')

    def __str__(self):
        return f"{self.client.name} @ {self.tenant.name}"


class ClientOTP(models.Model):
    """
    Código de verificação enviado via WhatsApp.
    TTL: 10 minutos.
    """
    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    phone      = models.CharField(max_length=20)
    code       = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'client_otps'
        indexes  = [models.Index(fields=['tenant', 'phone', 'used'])]

    def __str__(self):
        return f"OTP {self.phone} — {'usado' if self.used else 'pendente'}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at