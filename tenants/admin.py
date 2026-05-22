# tenants/admin.py

from django.contrib import admin
from .models import Tenant, TenantUser, EmailVerification, TenantBusinessHours


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'slug', 'plan', 'is_active',
        'email_verified', 'setup_completed', 'trial_ends_at', 'created_at'
    ]
    list_filter   = ['plan', 'is_active', 'email_verified', 'setup_completed', 'type']
    search_fields = ['name', 'slug', 'email', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at', 'trial_days_remaining',
                       'is_trial_active', 'max_professionals']
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'slug', 'name', 'type')
        }),
        ('Contato', {
            'fields': ('phone', 'email', 'address', 'city', 'logo_url')
        }),
        ('Plano e status', {
            'fields': (
                'plan', 'is_active', 'trial_ends_at',
                'trial_days_remaining', 'max_professionals'
            )
        }),
        ('Onboarding', {
            'fields': ('email_verified', 'setup_completed')
        }),
        ('WhatsApp', {
            'fields': ('wa_phone_number_id', 'wa_token', 'wa_verify_token'),
            'classes': ('collapse',),
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    actions = ['activate_plan_features_action']

    def activate_plan_features_action(self, request, queryset):
        for tenant in queryset:
            tenant.activate_plan_features()
        self.message_user(request, f"{queryset.count()} tenant(s) atualizados.")
    activate_plan_features_action.short_description = "Ativar features do plano"


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display  = ['user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter   = ['role', 'is_active']
    search_fields = ['user__email', 'tenant__name']
    raw_id_fields = ['user', 'tenant']


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'verified', 'verified_at', 'expires_at', 'created_at']
    list_filter   = ['verified']
    search_fields = ['user__email']
    readonly_fields = ['token', 'created_at']


@admin.register(TenantBusinessHours)
class TenantBusinessHoursAdmin(admin.ModelAdmin):
    list_display  = ['tenant', 'weekday', 'open_time', 'close_time', 'is_closed']
    list_filter   = ['is_closed', 'weekday']
    search_fields = ['tenant__name']