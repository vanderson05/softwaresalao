# agent/prompt.py
# Gerador dinâmico do system prompt por tenant
# Chamado a cada mensagem para garantir dados sempre atualizados

from tenants.models import TenantBusinessHours


TONE_MAP = {
    'friendly': 'amigável, descontraído e simpático. Use linguagem leve e emojis com moderação',
    'formal':   'profissional e formal. Use linguagem respeitosa, sem gírias ou emojis',
    'casual':   'casual e informal. Pode usar gírias leves e emojis à vontade',
}

WEEKDAY_NAMES = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']


def build_system_prompt(tenant, agent_config) -> str:
    """
    Monta o system prompt completo para o tenant.

    Dados dinâmicos injetados:
    - Serviços com preços e duração (sempre atualizados do banco)
    - Horários de funcionamento
    - Endereço e nome do estabelecimento
    - Nome, tom e regras de escalonamento do AgentConfig
    """
    from agenda.models import Service, Professional

    # ── Serviços ──────────────────────────────────────────────
    services = Service.objects.filter(tenant=tenant, is_active=True)
    if services.exists():
        services_lines = [
            f"  - {s.name}: R${s.price:.2f} ({s.duration_min} minutos)"
            for s in services
        ]
        services_text = '\n'.join(services_lines)
    else:
        services_text = "  (Nenhum serviço cadastrado)"

    # ── Profissionais ─────────────────────────────────────────
    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    if professionals.exists():
        prof_lines = [f"  - {p.name}" for p in professionals]
        prof_text  = '\n'.join(prof_lines)
    else:
        prof_text = "  (Nenhum profissional cadastrado)"

    # ── Horários de funcionamento ─────────────────────────────
    hours = TenantBusinessHours.objects.filter(tenant=tenant).order_by('weekday')
    if hours.exists():
        hours_lines = []
        for h in hours:
            day = WEEKDAY_NAMES[h.weekday]
            if h.is_closed:
                hours_lines.append(f"  - {day}: Fechado")
            elif h.open_time and h.close_time:
                hours_lines.append(
                    f"  - {day}: {h.open_time.strftime('%H:%M')}–{h.close_time.strftime('%H:%M')}"
                )
        hours_text = '\n'.join(hours_lines) if hours_lines else "  (Não configurado)"
    else:
        hours_text = "  (Não configurado)"

    # ── Tom de voz ────────────────────────────────────────────
    tone_desc = TONE_MAP.get(agent_config.tone, TONE_MAP['friendly'])

    # ── Endereço ──────────────────────────────────────────────
    address = f"{tenant.address}, {tenant.city}" if tenant.address else tenant.city or "Não informado"

    # ── Tipo do estabelecimento ───────────────────────────────
    type_map = {
        'barbershop': 'barbearia',
        'salon':      'salão de beleza',
        'studio':     'studio',
    }
    establishment_type = type_map.get(tenant.type, 'estabelecimento')

    # ── Prompt final ──────────────────────────────────────────
    prompt = f"""Você é {agent_config.agent_name}, assistente virtual da {establishment_type} {tenant.name}.
Seu tom é {tone_desc}.
Responda SEMPRE em português do Brasil.
Seja direto e objetivo — máximo 3 parágrafos por mensagem.

━━━ ESTABELECIMENTO ━━━
Nome: {tenant.name}
Endereço: {address}
Tipo: {establishment_type.title()}

━━━ SERVIÇOS DISPONÍVEIS ━━━
{services_text}

━━━ PROFISSIONAIS ━━━
{prof_text}

━━━ HORÁRIO DE FUNCIONAMENTO ━━━
{hours_text}

━━━ REGRAS OBRIGATÓRIAS ━━━
1. Para consultar horários: USE get_available_slots — NUNCA invente horários
2. Para criar agendamento: USE create_appointment — obrigatório após coletar todos os dados
3. Para cancelar: USE cancel_appointment com o telefone do cliente
4. Se o cliente digitar "{agent_config.escalate_keyword}": diga "Vou chamar nossa equipe! Um momento 😊" e encerre
5. Nunca invente preços, serviços ou horários fora do cadastro acima
6. Nunca mencione que você é uma IA ou usa ChatGPT

━━━ FLUXO OBRIGATÓRIO DE AGENDAMENTO ━━━
Siga EXATAMENTE esta ordem. Não pule etapas, não volte atrás.

ETAPA 1 — Serviço: pergunte qual serviço o cliente deseja
ETAPA 2 — Horários: chame get_available_slots e mostre as opções
ETAPA 3 — Escolha: cliente escolhe data e hora
ETAPA 4 — Nome: pergunte o nome completo do cliente
ETAPA 5 — Telefone: pergunte o telefone WhatsApp
ETAPA 6 — GRAVAR: você JÁ TEM serviço + horário + nome + telefone.
          CHAME IMEDIATAMENTE create_appointment. NÃO peça confirmação.
          NÃO chame get_available_slots novamente.
          NÃO mostre resumo antes de gravar.
          GRAVE e depois mostre o resumo do que foi agendado.

REGRA CRÍTICA DA ETAPA 6:
Quando você tiver: serviço escolhido + horário escolhido + nome + telefone
→ CHAME create_appointment IMEDIATAMENTE
→ Isso é obrigatório. Não há exceção."""

    return prompt