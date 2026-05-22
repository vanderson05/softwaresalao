# agenda/serializers_appointment.py
# Adicionar ao agenda/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Appointment, Professional, Service


class AppointmentCreateSerializer(serializers.Serializer):
    """
    Serializer para criação de agendamento.
    Usado pelos 3 canais: painel, link público e agente WhatsApp.
    """
    professional_id = serializers.UUIDField()
    service_id      = serializers.UUIDField()
    starts_at       = serializers.DateTimeField()
    client_name     = serializers.CharField(max_length=100)
    client_phone    = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes           = serializers.CharField(required=False, allow_blank=True)
    source          = serializers.ChoiceField(
        choices=['whatsapp', 'panel', 'link'],
        default='panel'
    )

    def validate_professional_id(self, value):
        request = self.context.get('request')
        tenant  = getattr(request, 'tenant', None)
        try:
            self.professional = Professional.objects.get(
                id=value, tenant=tenant, is_active=True
            )
        except Professional.DoesNotExist:
            raise serializers.ValidationError("Profissional não encontrado.")
        return value

    def validate_service_id(self, value):
        request = self.context.get('request')
        tenant  = getattr(request, 'tenant', None)
        try:
            self.service = Service.objects.get(
                id=value, tenant=tenant, is_active=True
            )
        except Service.DoesNotExist:
            raise serializers.ValidationError("Serviço não encontrado.")
        return value

    def validate_starts_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("O horário deve ser no futuro.")
        return value

    def validate(self, data):
        # Verifica se o profissional realiza o serviço
        if hasattr(self, 'professional') and hasattr(self, 'service'):
            services = self.professional.get_services()
            if not services.filter(id=self.service.id).exists():
                raise serializers.ValidationError(
                    "Este profissional não realiza este serviço."
                )

        # Verifica se o slot está disponível
        if hasattr(self, 'professional') and hasattr(self, 'service'):
            from .slots import get_available_slots
            from datetime import timedelta

            starts_at  = data['starts_at']
            check_date = starts_at.date()
            slots      = get_available_slots(self.professional, self.service, check_date)
            slot_times = [s['time'] for s in slots]
            requested  = starts_at.strftime('%H:%M')

            if requested not in slot_times:
                raise serializers.ValidationError(
                    f"Horário {requested} não está disponível. "
                    f"Horários disponíveis: {', '.join(slot_times[:5])}{'...' if len(slot_times) > 5 else ''}"
                )

        return data

    def create(self, validated_data):
        from datetime import timedelta
        from django.utils import timezone

        request    = self.context.get('request')
        tenant     = request.tenant
        source     = validated_data['source']
        starts_at  = validated_data['starts_at']
        ends_at    = starts_at + timedelta(minutes=self.service.duration_min)

        # Define status baseado na origem e auto_confirm
        try:
            auto_confirm = tenant.agent_config.auto_confirm
        except Exception:
            auto_confirm = True

        if source == 'panel':
            status = Appointment.Status.CONFIRMED  # barbeiro sempre confirma
        elif auto_confirm:
            status = Appointment.Status.CONFIRMED
        else:
            status = Appointment.Status.PENDING

        appointment = Appointment.objects.create(
            tenant         = tenant,
            professional   = self.professional,
            service        = self.service,
            client_name    = validated_data['client_name'],
            client_phone   = validated_data.get('client_phone', ''),
            starts_at      = starts_at,
            ends_at        = ends_at,
            status         = status,
            source         = source,
            price_snapshot = self.service.price,
            notes          = validated_data.get('notes', ''),
        )

        # Auto-cadastra cliente se vier phone
        if validated_data.get('client_phone'):
            self._upsert_client(tenant, appointment)

        return appointment

    def _upsert_client(self, tenant, appointment):
        """Cria ou atualiza o cliente automaticamente."""
        try:
            from clients.models import Client
            client, _ = Client.objects.get_or_create(
                tenant=tenant,
                phone=appointment.client_phone,
                defaults={'name': appointment.client_name}
            )
            appointment.client = client
            appointment.save(update_fields=['client'])
        except Exception:
            pass


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer de leitura completo."""
    professional_name = serializers.CharField(source='professional.name', read_only=True)
    service_name      = serializers.CharField(source='service.name', read_only=True)
    service_duration  = serializers.IntegerField(source='service.duration_min', read_only=True)
    status_display    = serializers.CharField(source='get_status_display', read_only=True)
    source_display    = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:
        model  = Appointment
        fields = [
            'id', 'client_name', 'client_phone',
            'professional', 'professional_name',
            'service', 'service_name', 'service_duration',
            'starts_at', 'ends_at',
            'status', 'status_display',
            'source', 'source_display',
            'price_snapshot', 'notes',
            'reminder_24h_sent', 'reminder_2h_sent', 'nps_sent',
            'created_at',
        ]
        read_only_fields = fields


class AppointmentListSerializer(serializers.ModelSerializer):
    """Versão resumida para listagem da agenda do dia."""
    professional_name = serializers.CharField(source='professional.name', read_only=True)
    service_name      = serializers.CharField(source='service.name', read_only=True)
    status_display    = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model  = Appointment
        fields = [
            'id', 'client_name', 'client_phone',
            'professional_name', 'service_name',
            'starts_at', 'ends_at',
            'status', 'status_display', 'source',
            'price_snapshot',
        ]