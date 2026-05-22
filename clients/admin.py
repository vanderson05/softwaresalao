from django.contrib import admin
from .models import Client, ClientTenantProfile, ClientOTP

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone']

@admin.register(ClientTenantProfile)
class ClientTenantProfileAdmin(admin.ModelAdmin):
    list_display  = ['client', 'tenant', 'loyalty_points', 'total_visits', 'last_visit_at']
    list_filter   = ['tenant']
    search_fields = ['client__name', 'client__phone']

@admin.register(ClientOTP)
class ClientOTPAdmin(admin.ModelAdmin):
    list_display  = ['phone', 'tenant', 'used', 'expires_at', 'created_at']
    list_filter   = ['used', 'tenant']