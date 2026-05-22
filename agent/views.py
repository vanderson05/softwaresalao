# ════════════════════════════════════════════════════════════════
# agent/views.py
# Views do painel — configuração e histórico de conversas
# ════════════════════════════════════════════════════════════════
 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
 
from tenants.permissions import TenantAccessPermission, IsOwnerOrManager
from .models import AgentConfig, Conversation
 
 
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([TenantAccessPermission])
def agent_config_view(request):
    """
    GET   /api/agent/config/  → retorna config atual do agente
    PATCH /api/agent/config/  → atualiza campos configuráveis pelo barbeiro
    """
    tenant = request.tenant
 
    try:
        config = AgentConfig.objects.get(tenant=tenant)
    except AgentConfig.DoesNotExist:
        config = AgentConfig.objects.create(tenant=tenant)
 
    if request.method == 'GET':
        return Response({
            'agent_name':        config.agent_name,
            'tone':              config.tone,
            'welcome_message':   config.welcome_message,
            'auto_confirm':      config.auto_confirm,
            'escalate_keyword':  config.escalate_keyword,
            'is_active':         config.is_active,
            'is_wa_connected':   config.is_whatsapp_connected,
            'messages_this_month': config.messages_this_month,
            'max_messages_month':  config.max_messages_month,
        })
 
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)
 
    # Campos que o barbeiro pode editar
    allowed = ['agent_name', 'tone', 'welcome_message', 'auto_confirm', 'escalate_keyword']
    changed = []
    for field in allowed:
        if field in request.data:
            setattr(config, field, request.data[field])
            changed.append(field)
 
    if changed:
        config.save(update_fields=changed + ['updated_at'])
 
    return Response({
        'message':       'Configurações do agente atualizadas.',
        'agent_name':    config.agent_name,
        'tone':          config.tone,
        'auto_confirm':  config.auto_confirm,
    })
 
 
@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def agent_conversations_view(request):
    """
    GET /api/agent/conversations/
    Lista conversas recentes do tenant com paginação.
    """
    tenant = request.tenant
    status_filter = request.query_params.get('status', 'active')
 
    conversations = Conversation.objects.filter(
        tenant=tenant
    )
 
    if status_filter != 'all':
        conversations = conversations.filter(status=status_filter)
 
    conversations = conversations.order_by('-last_msg_at')[:50]
 
    return Response([
        {
            'id':          str(c.id),
            'client_phone': c.client_phone,
            'client_name':  c.client_name,
            'status':       c.status,
            'msg_count':    c.msg_count,
            'started_at':   c.started_at.isoformat(),
            'last_msg_at':  c.last_msg_at.isoformat(),
            'appointment':  str(c.appointment_id) if c.appointment_id else None,
        }
        for c in conversations
    ])
 
 
@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def agent_conversation_detail_view(request, conversation_id):
    """
    GET /api/agent/conversations/{id}/
    Histórico completo de uma conversa.
    """
    tenant = request.tenant
 
    try:
        conv = Conversation.objects.get(id=conversation_id, tenant=tenant)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversa não encontrada.'}, status=404)
 
    return Response({
        'id':           str(conv.id),
        'client_phone': conv.client_phone,
        'client_name':  conv.client_name,
        'status':       conv.status,
        'msg_count':    conv.msg_count,
        'history':      conv.history,
        'started_at':   conv.started_at.isoformat(),
        'last_msg_at':  conv.last_msg_at.isoformat(),
    })
 
 
@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def agent_test_view(request):
    """
    POST /api/agent/test/
    Testa o agente sem passar pelo WhatsApp.
    Usado para validar o prompt e as funções antes de conectar o número.
 
    Body: {"message": "Oi quero agendar"}
    """
    from .engine import process_message, get_or_create_conversation
 
    tenant  = request.tenant
    message = request.data.get('message', '').strip()
 
    if not message:
        return Response({'error': 'message obrigatório.'}, status=400)
 
    try:
        config = AgentConfig.objects.get(tenant=tenant)
    except AgentConfig.DoesNotExist:
        return Response({'error': 'AgentConfig não encontrado.'}, status=404)
 
    # Usa número de teste para não misturar com conversas reais
    test_phone   = f"TEST_{request.user.id}"
    conversation = get_or_create_conversation(tenant, test_phone)
 
    reply = process_message(tenant, config, conversation, message)
 
    return Response({
        'message': message,
        'reply':   reply,
        'history': conversation.history[-6:],  # últimas 3 trocas
    })