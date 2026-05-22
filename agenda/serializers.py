# agenda/serializers.py

from rest_framework import serializers
from .models import Professional, Service, Schedule, ScheduleBlock


# ── Professional ──────────────────────────────────────────────────────────────

class ProfessionalSerializer(serializers.ModelSerializer):
    services_count = serializers.SerializerMethodField()

    class Meta:
        model  = Professional
        fields = [
            'id', 'name', 'photo_url', 'bio',
            'commission_pct', 'slot_interval',
            'is_active', 'services_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'services_count']

    def get_services_count(self, obj):
        return obj.get_services().count()

    def validate_commission_pct(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Comissão deve ser entre 0 e 100%.")
        return value

    def validate_slot_interval(self, value):
        valid = [15, 30, 45, 60]
        if value not in valid:
            raise serializers.ValidationError(f"Intervalo deve ser um de: {valid}")
        return value


class ProfessionalListSerializer(serializers.ModelSerializer):
    """Versão resumida para listagem."""
    class Meta:
        model  = Professional
        fields = ['id', 'name', 'photo_url', 'slot_interval', 'is_active']


# ── Service ───────────────────────────────────────────────────────────────────

class ServiceSerializer(serializers.ModelSerializer):
    professional_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
        help_text="IDs dos profissionais. Vazio = todos herdam."
    )
    professionals    = ProfessionalListSerializer(many=True, read_only=True)
    is_shared        = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Service
        fields = [
            'id', 'name', 'description', 'duration_min', 'price',
            'professional_ids', 'professionals', 'is_shared',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'professionals', 'is_shared']

    def validate_duration_min(self, value):
        if value < 5:
            raise serializers.ValidationError("Duração mínima é 5 minutos.")
        if value > 480:
            raise serializers.ValidationError("Duração máxima é 480 minutos (8 horas).")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Preço não pode ser negativo.")
        return value

    def validate_professional_ids(self, value):
        """Valida que os profissionais pertencem ao tenant."""
        if not value:
            return value

        request = self.context.get('request')
        tenant  = getattr(request, 'tenant', None)
        if not tenant:
            return value

        valid_ids = set(
            Professional.objects.filter(
                tenant=tenant, is_active=True
            ).values_list('id', flat=True)
        )

        invalid = [str(pid) for pid in value if pid not in valid_ids]
        if invalid:
            raise serializers.ValidationError(
                f"Profissionais não encontrados: {', '.join(invalid)}"
            )
        return value

    def create(self, validated_data):
        professional_ids = validated_data.pop('professional_ids', [])
        service          = Service.objects.create(**validated_data)

        if professional_ids:
            professionals = Professional.objects.filter(
                id__in=professional_ids,
                tenant=validated_data['tenant']
            )
            service.professionals.set(professionals)

        return service

    def update(self, instance, validated_data):
        professional_ids = validated_data.pop('professional_ids', None)
        instance = super().update(instance, validated_data)

        if professional_ids is not None:
            if professional_ids:
                professionals = Professional.objects.filter(
                    id__in=professional_ids,
                    tenant=instance.tenant
                )
                instance.professionals.set(professionals)
            else:
                instance.professionals.clear()  # vazio = herança por todos

        return instance


# ── Schedule ──────────────────────────────────────────────────────────────────

class ScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(
        source='get_weekday_display', read_only=True
    )

    class Meta:
        model  = Schedule
        fields = [
            'id', 'professional', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'is_active',
        ]
        read_only_fields = ['id', 'weekday_display']

    def validate(self, data):
        start = data.get('start_time')
        end   = data.get('end_time')

        if start and end and end <= start:
            raise serializers.ValidationError(
                {'end_time': 'Horário de término deve ser após o início.'}
            )
        return data

    def validate_professional(self, value):
        """Garante que o profissional pertence ao tenant."""
        request = self.context.get('request')
        tenant  = getattr(request, 'tenant', None)
        if tenant and value.tenant != tenant:
            raise serializers.ValidationError("Profissional não pertence ao seu estabelecimento.")
        return value


class ScheduleBulkSerializer(serializers.Serializer):
    """
    Serializer para configurar múltiplos dias de uma vez.
    Usado no wizard de setup.

    Payload:
    {
        "professional_id": "uuid",
        "schedules": [
            {"weekday": 0, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
            ...
        ]
    }
    """
    professional_id = serializers.UUIDField()
    schedules       = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
    )

    def validate_professional_id(self, value):
        request    = self.context.get('request')
        tenant     = getattr(request, 'tenant', None)
        try:
            self.professional = Professional.objects.get(
                id=value, tenant=tenant, is_active=True
            )
        except Professional.DoesNotExist:
            raise serializers.ValidationError("Profissional não encontrado.")
        return value

    def validate_schedules(self, value):
        errors = []
        for i, s in enumerate(value):
            weekday    = s.get('weekday')
            start_time = s.get('start_time')
            end_time   = s.get('end_time')

            if weekday is None or weekday not in range(7):
                errors.append(f"Item {i}: weekday inválido (0–6).")
            if not start_time:
                errors.append(f"Item {i}: start_time obrigatório.")
            if not end_time:
                errors.append(f"Item {i}: end_time obrigatório.")

        if errors:
            raise serializers.ValidationError(errors)
        return value

    def save(self):
        from datetime import time as time_type

        professional = self.professional
        tenant       = professional.tenant
        created      = []
        updated      = []

        for s in self.validated_data['schedules']:
            weekday    = s['weekday']
            start_str  = s['start_time']
            end_str    = s['end_time']

            # Converte string para time
            start_time = time_type(*[int(x) for x in start_str.split(':')])
            end_time   = time_type(*[int(x) for x in end_str.split(':')])

            obj, was_created = Schedule.objects.update_or_create(
                professional=professional,
                weekday=weekday,
                defaults={
                    'tenant':     tenant,
                    'start_time': start_time,
                    'end_time':   end_time,
                    'is_active':  True,
                }
            )

            if was_created:
                created.append(obj)
            else:
                updated.append(obj)

        return {'created': len(created), 'updated': len(updated)}


# ── ScheduleBlock ─────────────────────────────────────────────────────────────

class ScheduleBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ScheduleBlock
        fields = [
            'id', 'professional', 'date',
            'start_time', 'end_time', 'reason',
            'is_full_day', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'is_full_day']

    def validate(self, data):
        start = data.get('start_time')
        end   = data.get('end_time')

        if start and not end:
            raise serializers.ValidationError(
                {'end_time': 'end_time obrigatório quando start_time informado.'}
            )
        if end and not start:
            raise serializers.ValidationError(
                {'start_time': 'start_time obrigatório quando end_time informado.'}
            )
        if start and end and end <= start:
            raise serializers.ValidationError(
                {'end_time': 'Horário de término deve ser após o início.'}
            )
        return data