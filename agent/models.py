from django.db import models
from tenants.models import Tenant

class AgentConfig(models.Model):
    tenant          = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='agent_config')
    agent_name      = models.CharField(max_length=50, default='Bia')
    welcome_message = models.TextField(default='Olá! Como posso ajudar?')
    tone            = models.CharField(max_length=20, default='friendly')
    auto_confirm    = models.BooleanField(default=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agent_configs'

    def __str__(self):
        return f'Agente {self.agent_name} — {self.tenant.name}'