# apps/tenants/serializers.py

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Tenant, TenantUser, EmailVerification


# ── Registro ─────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    # Dados do estabelecimento
    business_name = serializers.CharField(max_length=120)
    type          = serializers.ChoiceField(
        choices=['barbershop', 'salon', 'studio'],
        default='barbershop'
    )

    # Dados de acesso
    phone    = serializers.CharField(max_length=20)
    email    = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este e-mail já está cadastrado.")
        return value

    def validate_phone(self, value):
        # Remove tudo que não é dígito
        digits = ''.join(filter(str.isdigit, value))
        if len(digits) < 10 or len(digits) > 11:
            raise serializers.ValidationError("Telefone inválido. Use DDD + número (10 ou 11 dígitos).")
        return digits

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        from django.utils import timezone
        from datetime import timedelta

        # 1. Criar User Django
        user = User.objects.create_user(
            username=validated_data['email'].lower(),
            email=validated_data['email'].lower(),
            password=validated_data['password'],
            is_active=True,
        )

        # 2. Criar Tenant
        slug = Tenant.generate_unique_slug(validated_data['business_name'])
        tenant = Tenant.objects.create(
            name          = validated_data['business_name'],
            type          = validated_data['type'],
            phone         = validated_data['phone'],
            email         = validated_data['email'].lower(),
            slug          = slug,
            plan          = 'trial',
            trial_ends_at = timezone.now() + timedelta(days=14),
            is_active     = True,
            email_verified = False,
            setup_completed = False,
        )

        # 3. Ativar features do trial (acesso total por 14 dias)
        tenant.activate_plan_features()

        # 4. Vincular User ao Tenant como owner
        TenantUser.objects.create(
            tenant = tenant,
            user   = user,
            role   = TenantUser.Role.OWNER,
        )

        # 5. Criar token de verificação de e-mail
        EmailVerification.objects.create(user=user)

        # 6. Criar AgentConfig padrão
        # Import aqui para evitar circular imports
        from agent.models import AgentConfig
        AgentConfig.objects.create(
            tenant     = tenant,
            agent_name = 'Bia',
        )

        return user, tenant


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate

        email    = data['email'].lower().strip()
        password = data['password']

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("E-mail ou senha incorretos.")

        if not user.is_active:
            raise serializers.ValidationError("Conta desativada. Entre em contato com o suporte.")

        # Busca o tenant ativo do usuário
        tenant_user = TenantUser.objects.filter(
            user=user, is_active=True
        ).select_related('tenant').first()

        if not tenant_user:
            raise serializers.ValidationError("Nenhum estabelecimento encontrado para este usuário.")

        tenant = tenant_user.tenant

        if not tenant.is_active:
            raise serializers.ValidationError("Estabelecimento inativo.")

        data['user']        = user
        data['tenant']      = tenant
        data['tenant_user'] = tenant_user
        return data

    def get_tokens(self, user, tenant, tenant_user):
        """
        Gera JWT com claims customizados do tenant.
        O middleware usa esses claims para injetar request.tenant.
        """
        refresh = RefreshToken.for_user(user)

        # Claims customizados no token
        refresh['tenant_id']   = str(tenant.id)
        refresh['tenant_slug'] = tenant.slug
        refresh['role']        = tenant_user.role
        refresh['plan']        = tenant.plan

        return {
            'refresh': str(refresh),
            'access':  str(refresh.access_token),
        }


# ── Verificação de e-mail ────────────────────────────────────────────────────

class EmailVerifySerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            verification = EmailVerification.objects.select_related('user').get(token=value)
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("Token inválido.")

        if verification.verified:
            raise serializers.ValidationError("E-mail já verificado.")

        if verification.is_expired:
            raise serializers.ValidationError("Token expirado. Solicite um novo e-mail de verificação.")

        self.verification = verification
        return value

    def save(self):
        from django.utils import timezone

        verification = self.verification
        verification.verified    = True
        verification.verified_at = timezone.now()
        verification.save()

        # Marca e-mail verificado no tenant
        tenant_user = TenantUser.objects.filter(
            user=verification.user, is_active=True
        ).select_related('tenant').first()

        if tenant_user:
            tenant_user.tenant.email_verified = True
            tenant_user.tenant.save(update_fields=['email_verified'])

        return verification.user


# ── Reenvio de verificação ───────────────────────────────────────────────────

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        value = value.lower().strip()
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            # Não revela se e-mail existe ou não (segurança)
            raise serializers.ValidationError("Se este e-mail estiver cadastrado, você receberá um novo link.")
        return value

    def save(self):
        import uuid
        from django.utils import timezone
        from datetime import timedelta

        user = self.user
        verification, _ = EmailVerification.objects.get_or_create(user=user)

        if verification.verified:
            return None  # Já verificado, não faz nada

        # Gera novo token e renova expiração
        verification.token      = uuid.uuid4()
        verification.expires_at = timezone.now() + timedelta(hours=24)
        verification.save()

        return verification


# ── Tenant público (resposta do registro) ────────────────────────────────────

class TenantBasicSerializer(serializers.ModelSerializer):
    trial_days_remaining = serializers.IntegerField(read_only=True)
    max_professionals    = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Tenant
        fields = [
            'id', 'slug', 'name', 'type', 'phone', 'email',
            'plan', 'is_active', 'trial_ends_at', 'trial_days_remaining',
            'email_verified', 'setup_completed', 'max_professionals',
            'created_at',
        ]
        read_only_fields = [
            'id', 'slug', 'plan', 'is_active', 'trial_ends_at',
            'email_verified', 'created_at',
        ]