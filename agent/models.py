# agent/models.py

import uuid
from django.db import models
from tenants.models import Tenant


class AgentConfig(models.Model):
    """
    Configuração do agente IA por tenant.
    Campos configuráveis pelo barbeiro no painel.
    Campos internos controlados só por você.
    """

    class Tone(models.TextChoices):
        FRIENDLY = 'friendly', 'Amigável e descontraído'
        FORMAL   = 'formal',   'Profissional e formal'
        CASUAL   = 'casual',   'Casual e informal'

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name='agent_config'
    )

    # ── Configurável pelo barbeiro ────────────────────────────
    agent_name      = models.CharField(max_length=50, default='Bia')
    tone            = models.CharField(max_length=20, choices=Tone.choices, default=Tone.FRIENDLY)
    welcome_message = models.TextField(
        default='Olá! Como posso ajudar?',
        help_text="Use {agent_name} e {business_name} como variáveis."
    )
    auto_confirm       = models.BooleanField(default=True)
    escalate_keyword   = models.CharField(
        max_length=50, default='humano',
        help_text="Palavra que transfere para atendimento humano."
    )

    # ── Interno — controlado só por você ─────────────────────
    max_messages_month = models.PositiveIntegerField(
        default=500,
        help_text="Limite de mensagens por mês para controle de custo."
    )
    messages_this_month = models.PositiveIntegerField(default=0)
    is_active           = models.BooleanField(default=True)

    # ── WhatsApp — Meta Cloud API ─────────────────────────────
    wa_phone_number_id = models.CharField(max_length=50, blank=True)
    wa_token           = models.TextField(blank=True)
    wa_verify_token    = models.CharField(
        max_length=100, blank=True,
        help_text="Token de verificação do webhook Meta."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'agent_configs'
        verbose_name = 'Configuração do agente'

    def __str__(self):
        return f"Agente {self.agent_name} — {self.tenant.name}"

    def get_welcome_message(self):
        """Resolve variáveis na mensagem de boas-vindas."""
        return self.welcome_message.format(
            agent_name    = self.agent_name,
            business_name = self.tenant.name,
        )

    @property
    def is_whatsapp_connected(self):
        return bool(self.wa_phone_number_id and self.wa_token)

    @property
    def reached_message_limit(self):
        return self.messages_this_month >= self.max_messages_month


class Conversation(models.Model):
    """
    Sessão de conversa no WhatsApp.
    Persiste o histórico de mensagens para o GPT manter contexto.
    TTL implícito: conversations inativas há 24h são ignoradas.
    """

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Ativa'
        ESCALATED = 'escalated', 'Escalada para humano'
        CLOSED    = 'closed',    'Encerrada'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='conversations')
    client_phone = models.CharField(max_length=20)
    client_name  = models.CharField(max_length=100, blank=True)
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Histórico serializado para o GPT
    # Lista de dicts: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    history      = models.JSONField(default=list)

    # Referência ao agendamento gerado nesta conversa
    appointment  = models.ForeignKey(
        'agenda.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='conversations'
    )

    msg_count  = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_msg_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'conversations'
        ordering     = ['-last_msg_at']
        indexes      = [
            models.Index(fields=['tenant', 'client_phone']),
            models.Index(fields=['tenant', 'last_msg_at']),
        ]
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'

    def __str__(self):
        return f"{self.client_phone} — {self.tenant.name} ({self.status})"

    def add_message(self, role: str, content: str):
        """Adiciona mensagem ao histórico e incrementa contador."""
        self.history.append({'role': role, 'content': content})
        self.msg_count += 1
        # Mantém apenas as últimas 20 mensagens para não exceder contexto
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.save(update_fields=['history', 'msg_count', 'last_msg_at'])

    def get_history_for_gpt(self) -> list:
        """Retorna histórico formatado para a API da OpenAI."""
        return self.history

    @property
    def is_fresh(self):
        """Conversa ativa nas últimas 24h."""
        from django.utils import timezone
        from datetime import timedelta
        return (timezone.now() - self.last_msg_at).total_seconds() < 86400