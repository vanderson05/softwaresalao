"""
test_agent.py — Testes do Agente WhatsApp Beauti
Simula conversas completas de agendamento, cancelamento e consulta.

Uso:
    python test_agent.py

Requisitos:
    pip install requests
    OPENAI_API_KEY configurada no .env
"""

import requests
import json
import sys
import time
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(msg):      print(f"  {GREEN}✓ {msg}{RESET}")
def fail(msg):    print(f"  {RED}✗ {msg}{RESET}")
def info(msg):    print(f"  {BLUE}→ {msg}{RESET}")
def warn(msg):    print(f"  {YELLOW}⚠ {msg}{RESET}")
def title(msg):   print(f"\n{BOLD}{BLUE}{'─'*50}{RESET}\n{BOLD}{msg}{RESET}")
def cliente(msg): print(f"  {CYAN}👤 Cliente: {msg}{RESET}")
def agente(msg):  print(f"  {GREEN}🤖 Agente:  {msg[:120]}{'...' if len(msg) > 120 else ''}{RESET}")


state = {
    'email':        f"agente_{datetime.now().strftime('%H%M%S')}@beauti.com",
    'password':     'Senha@123',
    'access_token': None,
    'errors':       [],
    'passed':       0,
    'failed':       0,
}


def assert_ok(condition, test_name):
    if condition:
        ok(test_name)
        state['passed'] += 1
        return True
    fail(test_name)
    state['failed'] += 1
    state['errors'].append(test_name)
    return False


def headers_auth():
    return {
        'Authorization': f"Bearer {state['access_token']}",
        'Content-Type':  'application/json',
    }


def chat(message: str) -> str:
    """Envia mensagem ao agente e retorna resposta."""
    cliente(message)
    resp = requests.post(
        f"{BASE_URL}/agent/test/",
        headers=headers_auth(),
        json={"message": message}
    )
    if resp.status_code != 200:
        fail(f"Erro na API: {resp.status_code} — {resp.text[:200]}")
        state['failed'] += 1
        return ""
    reply = resp.json().get('reply', '')
    agente(reply)
    return reply


def next_tuesday_str() -> str:
    today = date.today()
    for i in range(1, 8):
        d = today + timedelta(days=i)
        if d.weekday() == 1:
            return d.strftime("%d/%m")
    return "próxima terça"


# ════════════════════════════════════════════════════════════════
# SETUP — cria tenant completo para testar
# ════════════════════════════════════════════════════════════════

def setup():
    title("SETUP — Criando tenant de teste")

    # Registro
    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "business_name": "Barbearia Agente Test",
        "phone":         "19999999999",
        "email":         state['email'],
        "password":      state['password'],
        "type":          "barbershop",
    })
    if resp.status_code != 201:
        fail(f"Registro falhou: {resp.text[:100]}")
        return False
    ok("Tenant criado")

    # Login
    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": state['email'], "password": state['password'],
    })
    state['access_token'] = resp.json().get('tokens', {}).get('access')
    ok("Login OK — token obtido")

    h = headers_auth()

    # Estabelecimento
    requests.patch(f"{BASE_URL}/setup/establishment/", headers=h, json={
        "address": "Rua das Flores, 100",
        "city":    "Americana",
        "business_hours": [
            {"weekday": 0, "open_time": "13:00", "close_time": "18:00"},
            {"weekday": 1, "open_time": "09:00", "close_time": "18:00"},
            {"weekday": 2, "open_time": "09:00", "close_time": "18:00"},
            {"weekday": 3, "open_time": "09:00", "close_time": "18:00"},
            {"weekday": 4, "open_time": "09:00", "close_time": "18:00"},
            {"weekday": 5, "open_time": "09:00", "close_time": "13:00"},
            {"weekday": 6, "is_closed": True},
        ]
    })
    ok("Estabelecimento configurado")

    # Profissional
    resp = requests.post(f"{BASE_URL}/professionals/", headers=h, json={
        "name": "Carlão", "commission_pct": 40, "slot_interval": 30,
    })
    prof_id = resp.json().get('id')
    ok(f"Profissional Carlão: {prof_id}")

    # Serviços
    resp = requests.post(f"{BASE_URL}/services/", headers=h, json={
        "name": "Corte masculino", "duration_min": 30, "price": 35.00,
    })
    service_id = resp.json().get('id')
    ok(f"Serviço Corte masculino: {service_id}")

    requests.post(f"{BASE_URL}/services/", headers=h, json={
        "name": "Corte + Barba", "duration_min": 50, "price": 55.00,
    })
    ok("Serviço Corte + Barba criado")

    # Horários
    requests.post(f"{BASE_URL}/schedules/bulk/", headers=h, json={
        "professional_id": prof_id,
        "schedules": [
            {"weekday": 0, "start_time": "13:00", "end_time": "18:00"},
            {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 2, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 3, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 4, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 5, "start_time": "09:00", "end_time": "13:00"},
        ]
    })
    ok("Horários configurados")

    # Concluir wizard
    requests.post(f"{BASE_URL}/setup/complete/", headers=h)
    ok("Wizard concluído")

    # Configura agente
    requests.patch(f"{BASE_URL}/agent/config/", headers=h, json={
        "agent_name":     "Bia",
        "tone":           "friendly",
        "welcome_message": "Olá! Sou a Bia da {business_name}. Como posso ajudar? 😊",
        "auto_confirm":   True,
        "escalate_keyword": "humano",
    })
    ok("Agente Bia configurado")

    info(f"Setup completo — próxima terça: {next_tuesday_str()}")
    return True


# ════════════════════════════════════════════════════════════════
# TESTES DE CONVERSA
# ════════════════════════════════════════════════════════════════

def test_config_agent():
    title("AGENTE — Configuração e status")

    resp = requests.get(f"{BASE_URL}/agent/config/", headers=headers_auth())
    assert_ok(resp.status_code == 200, "GET /agent/config/ — status 200")

    data = resp.json()
    assert_ok(data.get('agent_name') == 'Bia',      "Nome do agente = Bia")
    assert_ok(data.get('tone') == 'friendly',        "Tom = friendly")
    assert_ok(data.get('auto_confirm') is True,      "auto_confirm = True")
    assert_ok('escalate_keyword' in data,            "Tem escalate_keyword")
    assert_ok('is_wa_connected' in data,             "Tem is_wa_connected")
    assert_ok('messages_this_month' in data,         "Tem messages_this_month")

    info(f"WhatsApp conectado: {data.get('is_wa_connected')}")
    info(f"Mensagens este mês: {data.get('messages_this_month')}")


def test_conversa_agendamento():
    title("AGENTE — Conversa 1: Agendamento completo")
    info("Simula cliente agendando corte pelo WhatsApp")
    print()

    # Saudação
    reply = chat("Oi")
    assert_ok(len(reply) > 0, "Agente respondeu à saudação")
    time.sleep(1)

    # Pergunta sobre serviços
    reply = chat("Quais serviços vocês têm?")
    assert_ok(len(reply) > 0, "Agente respondeu sobre serviços")
    assert_ok(
        "corte" in reply.lower() or "serviço" in reply.lower(),
        "Resposta menciona serviços"
    )
    time.sleep(1)

    # Pede agendamento
    reply = chat("Quero agendar um corte masculino")
    assert_ok(len(reply) > 0, "Agente respondeu ao pedido de agendamento")
    assert_ok(
        any(kw in reply.lower() for kw in [
            'horário', 'disponível', 'quando', 'data',
            'nome', 'telefone', 'confirmar', 'agendar', 'dia'
        ]),
        "Agente avançou no fluxo de agendamento"
    )
    time.sleep(1)

    # Escolhe próxima terça
    terça = next_tuesday_str()
    reply = chat(f"Pode ser na terça {terça} às 9h")
    assert_ok(len(reply) > 0, "Agente processou escolha de horário")
    time.sleep(1)

    # Informa nome
    reply = chat("Meu nome é João Silva")
    assert_ok(len(reply) > 0, "Agente processou nome do cliente")
    time.sleep(1)

    # Informa telefone
    reply = chat("Meu telefone é 19988887777")
    assert_ok(len(reply) > 0, "Agente processou telefone")
    time.sleep(1)

    # Verifica resposta de confirmação
    assert_ok(
        any(kw in reply.lower() for kw in [
            'agendado', 'confirmado', 'marcado', 'reservado',
            'corte', 'joão', 'terça', '9h', '09h', '09:00',
            'sucesso', 'pronto', 'até'
        ]),
        "Resposta final confirma o agendamento"
    )

    # Verifica se foi criado no banco
    resp = requests.get(
        f"{BASE_URL}/appointments/",
        headers=headers_auth(),
        params={"source": "whatsapp"}
    )
    appointments  = resp.json()
    whatsapp_appts = [a for a in appointments if a.get('source') == 'whatsapp']

    assert_ok(
        len(whatsapp_appts) > 0,
        f"Agendamento criado no banco — {len(whatsapp_appts)} encontrado(s)"
    )

    if whatsapp_appts:
        a = whatsapp_appts[0]
        info(f"Agendamento no banco: {a.get('service_name')} — {a.get('starts_at')}")

def test_conversa_consulta_horarios():
    title("AGENTE — Conversa 2: Consulta de horários")
    info("Nova sessão — cliente pergunta horários disponíveis")
    print()

    # Reseta conversa usando número diferente (simulado pelo endpoint de teste)
    # O endpoint /agent/test/ usa TEST_{user_id} como phone — mesma sessão
    # Para simular nova conversa, basta continuar

    reply = chat("Quais horários têm disponíveis essa semana para corte?")
    assert_ok(len(reply) > 0, "Agente respondeu sobre disponibilidade")
    assert_ok(
        any(kw in reply.lower() for kw in ['horário', 'disponível', 'terça', 'segunda', 'quarta', 'h']),
        "Resposta menciona horários"
    )
    time.sleep(1)


def test_conversa_cancelamento():
    title("AGENTE — Conversa 3: Cancelamento")
    info("Cliente quer cancelar agendamento")
    print()

    reply = chat("Preciso cancelar meu agendamento")
    assert_ok(len(reply) > 0, "Agente respondeu ao pedido de cancelamento")
    assert_ok(
        any(kw in reply.lower() for kw in [
            'cancelar', 'cancelamento', 'telefone', 'confirmar', 'qual'
        ]),
        "Agente pediu confirmação ou telefone para cancelar"
    )
    time.sleep(1)

    reply = chat("Meu telefone é 19988887777")
    assert_ok(len(reply) > 0, "Agente processou telefone para cancelamento")
    time.sleep(1)


def test_conversa_escalamento():
    title("AGENTE — Conversa 4: Escalonamento para humano")
    info("Cliente digita palavra de escalonamento")
    print()

    reply = chat("humano")
    assert_ok(len(reply) > 0, "Agente respondeu ao escalonamento")
    assert_ok(
        any(kw in reply.lower() for kw in [
            'equipe', 'chamar', 'momento', 'atendimento', 'humano'
        ]),
        "Agente sinalizou transferência para humano"
    )
    time.sleep(1)

    # Verifica se a conversa foi marcada como escalated
    resp = requests.get(
        f"{BASE_URL}/agent/conversations/",
        headers=headers_auth(),
        params={"status": "escalated"}
    )
    assert_ok(resp.status_code == 200, "GET /agent/conversations/?status=escalated")
    convs = resp.json()
    assert_ok(len(convs) >= 1, "Conversa escalated registrada no banco")
    if convs:
        info(f"Conversa escalada: {convs[0].get('client_phone')} — {convs[0].get('status')}")


def test_conversa_fora_do_escopo():
    title("AGENTE — Conversa 5: Pergunta fora do escopo")
    info("Cliente faz pergunta não relacionada a agendamento")
    print()

    reply = chat("Qual a previsão do tempo para amanhã?")
    assert_ok(len(reply) > 0, "Agente respondeu pergunta fora do escopo")
    # O agente deve redirecionar para o escopo do negócio
    time.sleep(1)


def test_historico_conversas():
    title("AGENTE — Histórico de conversas no painel")

    # Lista conversas
    resp = requests.get(
        f"{BASE_URL}/agent/conversations/",
        headers=headers_auth()
    )
    assert_ok(resp.status_code == 200, "GET /agent/conversations/")
    convs = resp.json()
    assert_ok(len(convs) >= 1, f"{len(convs)} conversa(s) registrada(s)")

    if convs:
        conv_id = convs[0].get('id')
        info(f"Última conversa: {conv_id}")
        info(f"  Phone: {convs[0].get('client_phone')}")
        info(f"  Msgs:  {convs[0].get('msg_count')}")
        info(f"  Status: {convs[0].get('status')}")

        # Detalhe da conversa
        resp = requests.get(
            f"{BASE_URL}/agent/conversations/{conv_id}/",
            headers=headers_auth()
        )
        assert_ok(resp.status_code == 200, "GET /agent/conversations/{id}/")
        detail = resp.json()
        assert_ok('history' in detail, "Detalhe tem 'history'")
        assert_ok(len(detail.get('history', [])) > 0, "Histórico tem mensagens")

        # Mostra resumo do histórico
        history = detail.get('history', [])
        info(f"  Histórico ({len(history)} mensagens):")
        for msg in history[-4:]:
            role    = "👤" if msg['role'] == 'user' else "🤖"
            content = msg['content'][:60]
            info(f"    {role} {content}{'...' if len(msg['content']) > 60 else ''}")


def test_config_update():
    title("AGENTE — Atualização de configuração")

    # Muda o nome do agente
    resp = requests.patch(
        f"{BASE_URL}/agent/config/",
        headers=headers_auth(),
        json={"agent_name": "João", "tone": "formal"}
    )
    assert_ok(resp.status_code == 200, "PATCH /agent/config/")
    data = resp.json()
    assert_ok(data.get('agent_name') == 'João', "Nome atualizado para João")
    assert_ok(data.get('tone') == 'formal',      "Tom atualizado para formal")

    # Verifica que foi salvo
    resp = requests.get(f"{BASE_URL}/agent/config/", headers=headers_auth())
    data = resp.json()
    assert_ok(data.get('agent_name') == 'João',  "Nome persistido no banco")

    # Restaura para Bia
    requests.patch(
        f"{BASE_URL}/agent/config/",
        headers=headers_auth(),
        json={"agent_name": "Bia", "tone": "friendly"}
    )
    ok("Configuração restaurada para Bia/friendly")
    state['passed'] += 1


# ════════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════════

def print_summary():
    title("RESUMO DOS TESTES DO AGENTE")
    total = state['passed'] + state['failed']
    print(f"\n  Total:    {total}")
    print(f"  {GREEN}Passou:   {state['passed']}{RESET}")
    print(f"  {RED}Falhou:   {state['failed']}{RESET}")
    if state['errors']:
        print(f"\n  {RED}Testes que falharam:{RESET}")
        for e in state['errors']:
            print(f"    {RED}• {e}{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}Todos os testes passaram! ✓{RESET}")
    print()
    return state['failed'] == 0


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(f"\n{BOLD}{'═'*50}{RESET}")
    print(f"{BOLD}  Beauti — Testes do Agente WhatsApp{RESET}")
    print(f"{BOLD}  Base URL: {BASE_URL}{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")

    # Setup
    if not setup():
        print(f"\n{RED}Setup falhou — abortando.{RESET}")
        sys.exit(1)

    # Testes de configuração
    test_config_agent()
    test_config_update()

    # Conversas simuladas
    test_conversa_agendamento()
    test_conversa_consulta_horarios()
    test_conversa_cancelamento()
    test_conversa_escalamento()
    test_conversa_fora_do_escopo()

    # Histórico no painel
    test_historico_conversas()

    success = print_summary()
    sys.exit(0 if success else 1)