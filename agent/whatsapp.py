# ════════════════════════════════════════════════════════════════
# agent/whatsapp.py
# Client para envio de mensagens via Meta WhatsApp Cloud API
# ════════════════════════════════════════════════════════════════
 
import requests
import logging
 
logger = logging.getLogger(__name__)
 
META_API_URL = "https://graph.facebook.com/v19.0"
 
 
def send_message(phone_number_id: str, wa_token: str, to: str, message: str) -> bool:
    """
    Envia mensagem de texto via Meta WhatsApp Cloud API.
 
    Args:
        phone_number_id: ID do número na Meta API
        wa_token:        Token de acesso
        to:              Número do destinatário (com DDI, sem +)
        message:         Texto da mensagem
 
    Returns:
        True se enviou com sucesso, False caso contrário
    """
    url     = f"{META_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                to,
        "type":              "text",
        "text":              {"body": message},
    }
 
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info(f"[WHATSAPP] Mensagem enviada para {to}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"[WHATSAPP ERROR] Erro ao enviar para {to}: {e}")
        return False
 
 
def mark_as_read(phone_number_id: str, wa_token: str, message_id: str) -> bool:
    """Marca mensagem como lida (double-check azul)."""
    url     = f"{META_API_URL}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {wa_token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status":            "read",
        "message_id":        message_id,
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False