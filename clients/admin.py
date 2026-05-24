# ════════════════════════════════════════════════════════════════
# clients/admin.py
# ════════════════════════════════════════════════════════════════
 
from django.contrib import admin
from .models import Client, ClientTenantProfile, ClientOTP, ClientSubscription
 
 
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display  = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']
 
 
@admin.register(ClientTenantProfile)
class ClientTenantProfileAdmin(admin.ModelAdmin):
    list_display  = ['client', 'tenant', 'loyalty_points', 'total_visits', 'last_visit_at']
    list_filter   = ['tenant']
    search_fields = ['client__name', 'client__phone']
    readonly_fields = ['created_at']
 
 
@admin.register(ClientOTP)
class ClientOTPAdmin(admin.ModelAdmin):
    list_display  = ['phone', 'tenant', 'used', 'expires_at', 'created_at']
    list_filter   = ['used', 'tenant']
    readonly_fields = ['created_at']
 
 
@admin.register(ClientSubscription)
class ClientSubscriptionAdmin(admin.ModelAdmin):
    list_display  = ['client', 'tenant', 'name', 'type', 'price', 'status', 'active_until']
    list_filter   = ['status', 'type', 'tenant']
    search_fields = ['client__name', 'client__phone', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']
 