# agenda/models.py

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from tenants.models import Tenant


class Professional(models.Model):
    """
    Barbeiro / profissional do estabelecimento.
    Cada profissional tem sua própria agenda e slot_interval.
    """

    SLOT_INTERVAL_CHOICES = [
        (15, '15 minutos'),
        (30, '30 minutos'),
        (45, '45 minutos'),
        (60, '60 minutos'),
        (90, '90 minutos'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant         = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='professionals')
    name           = models.CharField(max_length=100)
    photo_url      = models.URLField(blank=True)
    bio            = models.TextField(blank=True)
    commission_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Percentual de comissão. Ex: 40.00"
    )
    slot_interval  = models.PositiveIntegerField(
        choices=SLOT_INTERVAL_CHOICES,
        default=30,
        help_text="Intervalo mínimo entre agendamentos em minutos"
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professionals'
        ordering = ['name']
        verbose_name = 'Profissional'
        verbose_name_plural = 'Profissionais'

    def __str__(self):
        return f"{self.name} — {self.tenant.name}"

    def get_services(self):
        """
        Retorna serviços do profissional.
        Regra de herança:
          - Serviços explicitamente associados a este profissional
          - + Serviços sem nenhum profissional associado (herdados por todos)
        """
        from django.db.models import Q
        return Service.objects.filter(
            tenant=self.tenant,
            is_active=True
        ).filter(
            Q(professionals=self) | Q(professionals=None)
        ).distinct()


class Service(models.Model):
    """
    Serviço oferecido pelo estabelecimento.
    Se professionals estiver vazio → todos os profissionais herdam o serviço.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='services')
    name         = models.CharField(max_length=100)
    description  = models.TextField(blank=True)
    duration_min = models.PositiveIntegerField(
        help_text="Duração em minutos. Ex: 30, 60, 90"
    )
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    is_active    = models.BooleanField(default=True)

    # M2M com herança — vazio = todos os profissionais
    professionals = models.ManyToManyField(
        Professional,
        related_name='explicit_services',
        blank=True,
        help_text="Vazio = todos os profissionais do tenant herdam este serviço"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        ordering = ['name']
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

    def __str__(self):
        return f"{self.name} — R${self.price} ({self.duration_min}min)"

    @property
    def is_shared(self):
        """True se o serviço é herdado por todos (sem profissional específico)."""
        return not self.professionals.exists()


class Schedule(models.Model):
    """
    Horário de trabalho do profissional por dia da semana.
    Ausência permanente = simplesmente não ter Schedule para aquele dia.
    """
    WEEKDAYS = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='schedules')
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='schedules')
    weekday      = models.IntegerField(choices=WEEKDAYS)
    start_time   = models.TimeField()
    end_time     = models.TimeField()
    is_active    = models.BooleanField(default=True)

    class Meta:
        db_table        = 'schedules'
        unique_together = ('professional', 'weekday')
        ordering        = ['weekday', 'start_time']
        verbose_name    = 'Horário de trabalho'
        verbose_name_plural = 'Horários de trabalho'

    def __str__(self):
        return (
            f"{self.professional.name} — "
            f"{self.get_weekday_display()} "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )

    def clean(self):
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("Horário de término deve ser após o início.")


class ScheduleBlock(models.Model):
    """
    Bloqueio pontual de horário (folga, falta, reunião).
    start_time=None + end_time=None = dia inteiro bloqueado.
    """
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='schedule_blocks')
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='blocks')
    date         = models.DateField()
    start_time   = models.TimeField(null=True, blank=True, help_text="Null = dia inteiro bloqueado")
    end_time     = models.TimeField(null=True, blank=True)
    reason       = models.CharField(max_length=200, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'schedule_blocks'
        ordering = ['date', 'start_time']
        verbose_name = 'Bloqueio de horário'
        verbose_name_plural = 'Bloqueios de horário'

    def __str__(self):
        if not self.start_time:
            return f"{self.professional.name} — {self.date} (dia inteiro)"
        return f"{self.professional.name} — {self.date} {self.start_time}–{self.end_time}"

    @property
    def is_full_day(self):
        return self.start_time is None


class Appointment(models.Model):
    """
    Agendamento — núcleo do produto.
    """
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Aguardando confirmação'
        CONFIRMED = 'confirmed', 'Confirmado'
        COMPLETED = 'completed', 'Realizado'
        CANCELLED = 'cancelled', 'Cancelado'
        NO_SHOW   = 'no_show',   'Não compareceu'

    class Source(models.TextChoices):
        WHATSAPP = 'whatsapp', 'WhatsApp (agente IA)'
        PANEL    = 'panel',    'Painel (manual)'
        LINK     = 'link',     'Link público'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='appointments')
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='appointments')
    service      = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    client       = models.ForeignKey(
        'clients.Client', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='appointments'
    )
    client_name  = models.CharField(max_length=100, blank=True)
    client_phone = models.CharField(max_length=20, blank=True)

    starts_at = models.DateTimeField()
    ends_at   = models.DateTimeField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.WHATSAPP)

    price_snapshot = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    reminder_24h_sent = models.BooleanField(default=False)
    reminder_2h_sent  = models.BooleanField(default=False)
    nps_sent          = models.BooleanField(default=False)

    notes      = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['starts_at']
        indexes  = [
            models.Index(fields=['tenant', 'starts_at']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['professional', 'starts_at']),
        ]

    def __str__(self):
        name = self.client_name or (str(self.client) if self.client else 'Cliente')
        return f"{name} — {self.service.name} {self.starts_at:%d/%m %H:%M}"