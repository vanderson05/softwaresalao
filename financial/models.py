# ════════════════════════════════════════════════════════════════
# financial/models.py
# ════════════════════════════════════════════════════════════════
 
import uuid
from django.db import models
from tenants.models import Tenant
 
 
class CashEntry(models.Model):
 
    class PaymentMethod(models.TextChoices):
        PIX    = 'pix',    'Pix'
        CASH   = 'cash',   'Dinheiro'
        CREDIT = 'credit', 'Cartão de crédito'
        DEBIT  = 'debit',  'Cartão de débito'
        OTHER  = 'other',  'Outro'
 
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cash_entries')
    appointment  = models.OneToOneField(
        'agenda.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cash_entry'
    )
    professional = models.ForeignKey(
        'agenda.Professional', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    amount         = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.PIX
    )
    description = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'cash_entries'
        ordering = ['-created_at']
        indexes  = [models.Index(fields=['tenant', 'created_at'])]
 
    def __str__(self):
        return f"R${self.amount} — {self.created_at:%d/%m/%Y}"