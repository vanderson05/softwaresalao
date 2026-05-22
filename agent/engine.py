# agent/engine.py
# Motor principal do agente WhatsApp
# Orquestra GPT + function calling + histórico + resposta

import json
import os
import logging
from openai import OpenAI

from .prompt import build_system_prompt
from .functions import FUNCTION_DEFINITIONS, execute_function
from decouple import config as decouple_config
logger = logging.getLogger(__name__)

# Cliente OpenAI — inicializado uma vez
_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=decouple_config('OPENAI_API_KEY'))
    return _openai_client


def process_message(tenant, agent_config, conversation, user_message: str) -> str:
    """
    Motor principal. Recebe mensagem do cliente e retorna resposta do agente.

    Fluxo:
    1. Adiciona mensagem do cliente ao histórico
    2. Verifica escalonamento
    3. Chama GPT com system prompt dinâmico + histórico
    4. Se GPT retornar function call → executa → retorna resultado ao GPT
    5. Salva resposta no histórico
    6. Retorna texto final para envio via WhatsApp
    """

    # ── 1. Verifica escalonamento ─────────────────────────────
    if agent_config.escalate_keyword.lower() in user_message.lower():
        conversation.status = 'escalated'
        conversation.save(update_fields=['status'])
        reply = (
            f"Entendido! Vou chamar nossa equipe agora. "
            f"Um momento, por favor! 😊"
        )
        conversation.add_message('user',      user_message)
        conversation.add_message('assistant', reply)
        return reply

    # ── 2. Verifica limite de mensagens ───────────────────────
    if agent_config.reached_message_limit:
        return (
            "Nosso assistente está temporariamente indisponível. "
            "Por favor, entre em contato diretamente com a barbearia."
        )

    # ── 3. Monta o payload para o GPT ────────────────────────
    system_prompt = build_system_prompt(tenant, agent_config)

    messages = [
        {"role": "system", "content": system_prompt},
        *conversation.get_history_for_gpt(),
        {"role": "user", "content": user_message},
    ]

    # ── 4. Chama GPT com function calling ─────────────────────
    try:
        reply = _call_gpt_with_functions(messages, tenant)
    except Exception as e:
        logger.error(f"[AGENT ERROR] tenant={tenant.slug} error={e}")
        reply = (
            "Desculpe, tive um problema técnico. "
            "Por favor, tente novamente ou entre em contato com a barbearia."
        )

    # ── 5. Salva no histórico ─────────────────────────────────
    conversation.add_message('user',      user_message)
    conversation.add_message('assistant', reply)

    # ── 6. Incrementa contador de mensagens ───────────────────
    agent_config.messages_this_month += 1
    agent_config.save(update_fields=['messages_this_month'])

    return reply


def _call_gpt_with_functions(messages: list, tenant, max_iterations: int = 5) -> str:
    """
    Chama GPT e processa function calls em loop até obter resposta final.
    Máximo de 5 iterações para evitar loops infinitos.
    """
    client     = get_openai_client()
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        response = client.chat.completions.create(
            model       = "gpt-4o-mini",
            messages    = messages,
            tools       = [{"type": "function", "function": f} for f in FUNCTION_DEFINITIONS],
            tool_choice = "auto",
            temperature = 0.3,
            max_tokens  = 500,
        )

        message = response.choices[0].message

        # Sem function call → retorna texto final
        if not message.tool_calls:
            return message.content or "Desculpe, não consegui processar sua mensagem."

        # Processa todas as function calls
        messages.append({
            "role":       "assistant",
            "content":    message.content,
            "tool_calls": [
                {
                    "id":       tc.id,
                    "type":     "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in message.tool_calls
            ]
        })

        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            logger.info(f"[FUNCTION CALL] {func_name}({func_args})")

            result = execute_function(func_name, func_args, tenant)

            logger.info(f"[FUNCTION RESULT] {func_name} → {result[:200]}")

            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      result,
            })

    # Fallback após max iterações
    return "Desculpe, não consegui processar sua solicitação. Por favor, tente novamente."


def get_or_create_conversation(tenant, client_phone: str):
    """
    Busca conversa ativa ou cria nova.
    Conversa "fresca" = ativa nas últimas 24h.
    """
    from .models import Conversation
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(hours=24)

    conversation = Conversation.objects.filter(
        tenant       = tenant,
        client_phone = client_phone,
        status       = Conversation.Status.ACTIVE,
        last_msg_at__gte = cutoff,
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(
            tenant       = tenant,
            client_phone = client_phone,
            status       = Conversation.Status.ACTIVE,
            history      = [],
        )

    return conversation