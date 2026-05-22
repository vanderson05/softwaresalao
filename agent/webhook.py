# ════════════════════════════════════════════════════════════════
# agent/webhook.py
# View do webhook Meta — GET (verificação) e POST (mensagens)
# ════════════════════════════════════════════════════════════════
 
import json
import logging
import threading
 
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
 
from tenants.models import Tenant
from .models import AgentConfig
from .engine import process_message, get_or_create_conversation
from .whatsapp import send_message, mark_as_read
 
logger = logging.getLogger(__name__)
 
 
@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook_view(request):
    """
    GET  /webhook/  → verificação do webhook pela Meta
    POST /webhook/  → recebe mensagens dos clientes
    """
    if request.method == "GET":
        return _verify_webhook(request)
    return _receive_message(request)
 
 
def _verify_webhook(request):
    """
    Meta chama GET para verificar o webhook.
    Valida o verify_token e retorna o hub.challenge.
    """
    mode      = request.GET.get("hub.mode")
    token     = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")
 
    if mode == "subscribe" and challenge:
        # Busca o AgentConfig com este verify_token
        agent_config = AgentConfig.objects.filter(
            wa_verify_token=token
        ).first()
 
        if agent_config:
            logger.info(f"[WEBHOOK] Verificado para tenant: {agent_config.tenant.name}")
            return HttpResponse(challenge, content_type="text/plain")
 
    logger.warning(f"[WEBHOOK] Verificação falhou — token: {token}")
    return HttpResponse("Forbidden", status=403)
 
 
def _receive_message(request):
    """
    Meta chama POST com mensagens dos clientes.
    Processa de forma assíncrona para responder 200 imediatamente.
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
 
    # Responde 200 imediatamente para a Meta não reenviar
    # Processamento acontece em thread separada
    thread = threading.Thread(
        target=_process_webhook_payload,
        args=(body,),
        daemon=True
    )
    thread.start()
 
    return JsonResponse({"status": "ok"})
 
 
def _process_webhook_payload(body: dict):
    """
    Processa o payload do webhook em background.
    Identifica tenant → extrai mensagem → chama o agente → envia resposta.
    """
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
 
        # Ignora se não é mensagem
        if "messages" not in value:
            return
 
        messages         = value.get("messages", [])
        phone_number_id  = value.get("metadata", {}).get("phone_number_id", "")
 
        if not messages or not phone_number_id:
            return
 
        message_data = messages[0]
        msg_type     = message_data.get("type")
 
        # Só processa mensagens de texto por enquanto
        # (áudio = Sprint 3 — feature_audio_support)
        if msg_type != "text":
            logger.info(f"[WEBHOOK] Tipo não suportado: {msg_type}")
            return
 
        client_phone = message_data.get("from", "")
        message_id   = message_data.get("id", "")
        user_message = message_data.get("text", {}).get("body", "").strip()
 
        if not user_message or not client_phone:
            return
 
        # ── Identifica o tenant pelo phone_number_id ──────────
        try:
            agent_config = AgentConfig.objects.select_related('tenant').get(
                wa_phone_number_id=phone_number_id,
                is_active=True,
            )
        except AgentConfig.DoesNotExist:
            logger.warning(f"[WEBHOOK] Nenhum tenant para phone_number_id: {phone_number_id}")
            return
 
        tenant = agent_config.tenant
 
        # ── Verifica se tenant pode receber mensagens ─────────
        if not tenant.can_access:
            logger.info(f"[WEBHOOK] Tenant {tenant.slug} sem acesso")
            return
 
        # ── Marca como lida ───────────────────────────────────
        mark_as_read(phone_number_id, agent_config.wa_token, message_id)
 
        # ── Busca ou cria conversa ────────────────────────────
        conversation = get_or_create_conversation(tenant, client_phone)
 
        # Primeira mensagem — envia boas-vindas antes de processar
        if conversation.msg_count == 0:
            welcome = agent_config.get_welcome_message()
            send_message(phone_number_id, agent_config.wa_token, client_phone, welcome)
 
        # ── Processa com o motor do agente ─────────────────────
        reply = process_message(tenant, agent_config, conversation, user_message)
 
        # ── Envia resposta via WhatsApp ────────────────────────
        send_message(phone_number_id, agent_config.wa_token, client_phone, reply)
 
        logger.info(
            f"[WEBHOOK] tenant={tenant.slug} "
            f"from={client_phone} "
            f"msg='{user_message[:50]}' "
            f"reply='{reply[:50]}'"
        )
 
    except Exception as e:
        logger.error(f"[WEBHOOK ERROR] {e}", exc_info=True)