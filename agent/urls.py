# ════════════════════════════════════════════════════════════════
# agent/urls.py
# ════════════════════════════════════════════════════════════════
 
from django.urls import path
from .webhook import webhook_view
from . import views
 
urlpatterns = [
    # Webhook Meta — verificação e recebimento de mensagens
    path('webhook/', webhook_view, name='webhook'),
 
    # API do painel — configuração do agente pelo barbeiro
    path('agent/config/',         views.agent_config_view,        name='agent-config'),
    path('agent/conversations/',  views.agent_conversations_view, name='agent-conversations'),
    path('agent/conversations/<uuid:conversation_id>/',
         views.agent_conversation_detail_view,
         name='agent-conversation-detail'),
    path('agent/test/',           views.agent_test_view,          name='agent-test'),
]