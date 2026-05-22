# clients/models.py
import uuid
from django.db import models
from tenants.models import Tenant

class Client(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clients')
    name       = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'clients'
        unique_together = ('tenant', 'phone')

    def __str__(self):
        return f"{self.name} ({self.phone})"