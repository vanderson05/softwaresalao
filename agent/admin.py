# ════════════════════════════════════════════════════════════════
# agent/admin.py
# ════════════════════════════════════════════════════════════════
 
from django.contrib import admin
from .models import AgentConfig, Conversation
 
 
@admin.register(AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display = [
        'agent_name', 'tenant', 'tone', 'auto_confirm',
        'is_active', 'is_whatsapp_connected', 'messages_this_month'
    ]
    list_filter  = ['tone', 'auto_confirm', 'is_active']
    search_fields = ['agent_name', 'tenant__name']
    readonly_fields = ['messages_this_month', 'updated_at', 'is_whatsapp_connected']
    fieldsets = (
        ('Configurações do barbeiro', {
            'fields': ('tenant', 'agent_name', 'tone', 'welcome_message',
                       'auto_confirm', 'escalate_keyword')
        }),
        ('WhatsApp', {
            'fields': ('wa_phone_number_id', 'wa_token', 'wa_verify_token',
                       'is_whatsapp_connected'),
        }),
        ('Controle interno', {
            'fields': ('is_active', 'max_messages_month', 'messages_this_month', 'updated_at'),
        }),
    )
 
 
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display  = ['client_phone', 'tenant', 'status', 'msg_count', 'last_msg_at']
    list_filter   = ['status', 'tenant']
    search_fields = ['client_phone', 'client_name']
    readonly_fields = ['id', 'history', 'started_at', 'last_msg_at']