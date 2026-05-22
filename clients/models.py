# ════════════════════════════════════════════════════════════════
# clients/models.py  — versão completa
# ════════════════════════════════════════════════════════════════
 
import uuid
from django.db import models
from tenants.models import Tenant
 
 
class Client(models.Model):
 
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant    = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clients')
    name      = models.CharField(max_length=100)
    phone     = models.CharField(max_length=20)
    email     = models.EmailField(blank=True)
    birthdate = models.DateField(null=True, blank=True)
    notes     = models.TextField(blank=True)
 
    # Fidelização
    loyalty_points = models.PositiveIntegerField(default=0)
 
    # Controle de retenção
    last_visit_at      = models.DateTimeField(null=True, blank=True)
    return_msg_sent_at = models.DateTimeField(null=True, blank=True)
 
    # Aniversário
    birthday_msg_sent_year = models.PositiveIntegerField(null=True, blank=True)
 
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        db_table        = 'clients'
        unique_together = ('tenant', 'phone')
        ordering        = ['name']
        indexes         = [
            models.Index(fields=['tenant', 'phone']),
            models.Index(fields=['tenant', 'last_visit_at']),
        ]
 
    def __str__(self):
        return f"{self.name} ({self.phone})"
 
    @property
    def total_appointments(self):
        return self.appointments.filter(status='completed').count()
 
    @property
    def total_spent(self):
        from django.db.models import Sum
        return self.appointments.filter(
            status='completed'
        ).aggregate(total=Sum('price_snapshot'))['total'] or 0
 