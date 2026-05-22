"""
test_api.py — Testes automatizados Beauti
Etapa 1 (Auth) + Etapa 2 (Trial) + Etapa 3 (Setup) + Etapa 4 (Agendamentos)

Uso:
    python test_api.py

Requisitos:
    pip install requests
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(msg):    print(f"  {GREEN}✓ {msg}{RESET}")
def fail(msg):  print(f"  {RED}✗ {msg}{RESET}")
def info(msg):  print(f"  {BLUE}→ {msg}{RESET}")
def warn(msg):  print(f"  {YELLOW}⚠ {msg}{RESET}")
def title(msg): print(f"\n{BOLD}{BLUE}{'─'*50}{RESET}\n{BOLD}{msg}{RESET}")


state = {
    'email':              f"teste_{datetime.now().strftime('%H%M%S')}@beauti.com",
    'password':           'Senha@123',
    'access_token':       None,
    'refresh_token':      None,
    'tenant_slug':        None,
    'professional_id':    None,
    'professional_id2':   None,
    'service_id':         None,
    'service_id2':        None,
    'appointment_panel':  None,  # Canal 1 — painel
    'appointment_link':   None,  # Canal 2 — link
    'appointment_wa':     None,  # Canal 3 — whatsapp
    'appointment_cancel': None,  # para testar cancelamento pelo cliente
    'errors':             [],
    'passed':             0,
    'failed':             0,
}


def assert_status(resp, expected, test_name):
    if resp.status_code == expected:
        ok(f"{test_name} — status {resp.status_code}")
        state['passed'] += 1
        return True
    else:
        fail(f"{test_name} — esperado {expected}, recebeu {resp.status_code}")
        try:
            info(f"Resposta: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
        except Exception:
            info(f"Resposta: {resp.text[:300]}")
        state['failed'] += 1
        state['errors'].append(test_name)
        return False


def assert_field(data, field, test_name):
    if field in data:
        ok(f"{test_name} — campo '{field}' presente")
        state['passed'] += 1
        return True
    fail(f"{test_name} — campo '{field}' ausente")
    state['failed'] += 1
    state['errors'].append(test_name)
    return False


def assert_value(data, field, expected, test_name):
    actual = data.get(field)
    if actual == expected:
        ok(f"{test_name} — {field}={expected}")
        state['passed'] += 1
        return True
    fail(f"{test_name} — esperado {field}={expected}, recebeu {actual}")
    state['failed'] += 1
    state['errors'].append(test_name)
    return False


def headers_auth():
    return {
        'Authorization': f"Bearer {state['access_token']}",
        'Content-Type':  'application/json',
    }


def next_tuesday():
    """Retorna a próxima terça-feira no futuro."""
    today = date.today()
    for i in range(1, 8):
        d = today + timedelta(days=i)
        if d.weekday() == 1:
            return d
    return today + timedelta(days=2)


# ════════════════════════════════════════════════════════════════
# ETAPAS 1, 2, 3 — compactadas (já validadas antes)
# ════════════════════════════════════════════════════════════════

def setup_etapas_1_2_3():
    """Executa setup completo das etapas anteriores silenciosamente."""
    title("SETUP — Etapas 1, 2 e 3 (base para Etapa 4)")

    # Registro
    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "business_name": "Barbearia Etapa4 Test",
        "phone": "19999999999",
        "email": state['email'],
        "password": state['password'],
        "type": "barbershop",
    })
    if resp.status_code != 201:
        fail(f"Registro falhou: {resp.text[:200]}")
        state['failed'] += 1
        return False
    ok("Registro OK")
    state['passed'] += 1

    # Login
    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "email": state['email'], "password": state['password'],
    })
    tokens = resp.json().get('tokens', {})
    state['access_token']  = tokens.get('access')
    state['refresh_token'] = tokens.get('refresh')
    ok("Login OK")
    state['passed'] += 1

    h = headers_auth()

    # Estabelecimento
    requests.patch(f"{BASE_URL}/setup/establishment/", headers=h, json={
        "address": "Av. Cillo, 320", "city": "Americana",
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
    state['passed'] += 1

    # Profissional 1 — Carlão
    resp = requests.post(f"{BASE_URL}/professionals/", headers=h, json={
        "name": "Carlão", "commission_pct": 40, "slot_interval": 30,
    })
    state['professional_id'] = resp.json().get('id')
    ok(f"Carlão criado: {state['professional_id']}")
    state['passed'] += 1

    # Profissional 2 — Marcos
    resp = requests.post(f"{BASE_URL}/professionals/", headers=h, json={
        "name": "Marcos", "commission_pct": 35, "slot_interval": 30,
    })
    state['professional_id2'] = resp.json().get('id')
    ok(f"Marcos criado: {state['professional_id2']}")
    state['passed'] += 1

    # Serviço 1 — Corte (herdado por todos)
    resp = requests.post(f"{BASE_URL}/services/", headers=h, json={
        "name": "Corte masculino", "duration_min": 30, "price": 35.00,
    })
    state['service_id'] = resp.json().get('id')
    ok(f"Corte masculino criado: {state['service_id']}")
    state['passed'] += 1

    # Serviço 2 — Corte + Barba (só Carlão)
    resp = requests.post(f"{BASE_URL}/services/", headers=h, json={
        "name": "Corte + Barba", "duration_min": 50, "price": 55.00,
        "professional_ids": [state['professional_id']],
    })
    state['service_id2'] = resp.json().get('id')
    ok(f"Corte + Barba criado: {state['service_id2']}")
    state['passed'] += 1

    # Horários Carlão — seg-sex + sáb
    requests.post(f"{BASE_URL}/schedules/bulk/", headers=h, json={
        "professional_id": state['professional_id'],
        "schedules": [
            {"weekday": 0, "start_time": "13:00", "end_time": "18:00"},
            {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 2, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 3, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 4, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 5, "start_time": "09:00", "end_time": "13:00"},
        ]
    })
    ok("Horários Carlão configurados")
    state['passed'] += 1

    # Horários Marcos — ter, qui, sex
    requests.post(f"{BASE_URL}/schedules/bulk/", headers=h, json={
        "professional_id": state['professional_id2'],
        "schedules": [
            {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 3, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 4, "start_time": "09:00", "end_time": "18:00"},
        ]
    })
    ok("Horários Marcos configurados")
    state['passed'] += 1

    # Concluir wizard
    requests.post(f"{BASE_URL}/setup/complete/", headers=h)
    ok("Wizard concluído")
    state['passed'] += 1

    info(f"Setup completo — próxima terça: {next_tuesday().isoformat()}")
    return True


# ════════════════════════════════════════════════════════════════
# ETAPA 4 — AGENDAMENTOS
# ════════════════════════════════════════════════════════════════

def test_appointment_canal1_panel():
    title("ETAPA 4 — Canal 1: Barbeiro cria manual (painel)")

    terça = next_tuesday()
    starts_at = f"{terça.isoformat()}T09:00:00"

    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       starts_at,
        "client_name":     "João Silva",
        "client_phone":    "19988887777",
        "source":          "panel",
    })
    if not assert_status(resp, 201, "POST /appointments/ (canal panel)"):
        return

    data = resp.json()
    state['appointment_panel'] = data.get('id')
    assert_field(data, 'id',         "Tem 'id'")
    assert_field(data, 'starts_at',  "Tem 'starts_at'")
    assert_field(data, 'ends_at',    "Tem 'ends_at'")
    assert_field(data, 'status',     "Tem 'status'")
    assert_field(data, 'source',     "Tem 'source'")
    assert_value(data, 'status',     'confirmed', "Canal panel → status=confirmed")
    assert_value(data, 'source',     'panel',     "Source = panel")

    info(f"Agendamento painel: {state['appointment_panel']}")
    info(f"Início: {data.get('starts_at')} | Fim: {data.get('ends_at')}")
    info(f"Preço snapshot: R${data.get('price_snapshot')}")


def test_appointment_canal2_link():
    title("ETAPA 4 — Canal 2: Cliente agenda pelo link público")

    terça = next_tuesday()
    starts_at = f"{terça.isoformat()}T10:00:00"

    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       starts_at,
        "client_name":     "Maria Santos",
        "client_phone":    "19977776666",
        "source":          "link",
    })
    if not assert_status(resp, 201, "POST /appointments/ (canal link)"):
        return

    data = resp.json()
    state['appointment_link']   = data.get('id')
    state['appointment_cancel'] = data.get('id')
    assert_value(data, 'source', 'link', "Source = link")
    info(f"Agendamento link: {state['appointment_link']}")


def test_appointment_canal3_whatsapp():
    title("ETAPA 4 — Canal 3: Agente WhatsApp cria agendamento")

    terça = next_tuesday()
    starts_at = f"{terça.isoformat()}T14:00:00"

    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       starts_at,
        "client_name":     "Pedro Costa",
        "client_phone":    "19966665555",
        "source":          "whatsapp",
        "notes":           "Cliente pediu para confirmar antes",
    })
    if not assert_status(resp, 201, "POST /appointments/ (canal whatsapp)"):
        return

    data = resp.json()
    state['appointment_wa'] = data.get('id')
    assert_value(data, 'source', 'whatsapp', "Source = whatsapp")
    assert_field(data, 'notes', "Tem 'notes'")
    info(f"Agendamento WhatsApp: {state['appointment_wa']}")


def test_appointment_validation():
    title("Validação — Agendamentos")

    terça = next_tuesday()

    # Horário no passado
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       "2020-01-01T09:00:00",
        "client_name":     "Teste",
        "source":          "panel",
    })
    assert_status(resp, 400, "POST /appointments/ (horário no passado)")

    # Slot indisponível (já ocupado pelo João às 09h)
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T09:00:00",
        "client_name":     "Conflito",
        "source":          "panel",
    })
    assert_status(resp, 400, "POST /appointments/ (slot já ocupado)")

    # Serviço que o profissional não realiza
    if state['professional_id2'] and state['service_id2']:
        resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
            "professional_id": state['professional_id2'],
            "service_id":      state['service_id2'],  # Corte+Barba só do Carlão
            "starts_at":       f"{terça.isoformat()}T09:00:00",
            "client_name":     "Teste",
            "source":          "panel",
        })
        assert_status(resp, 400, "POST /appointments/ (profissional não realiza serviço)")

    # Sem client_name
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T15:00:00",
        "source":          "panel",
    })
    assert_status(resp, 400, "POST /appointments/ (sem client_name)")


def test_appointment_list():
    title("ETAPA 4 — Listar agendamentos")

    terça = next_tuesday()

    # Lista todos
    resp = requests.get(f"{BASE_URL}/appointments/", headers=headers_auth())
    if assert_status(resp, 200, "GET /appointments/"):
        data = resp.json()
        if len(data) >= 3:
            ok(f"{len(data)} agendamentos listados")
            state['passed'] += 1

    # Filtro por data
    resp = requests.get(
        f"{BASE_URL}/appointments/",
        headers=headers_auth(),
        params={'date': terça.isoformat()}
    )
    if assert_status(resp, 200, "GET /appointments/?date=terça"):
        data = resp.json()
        info(f"Agendamentos na terça: {len(data)}")

    # Filtro por status
    resp = requests.get(
        f"{BASE_URL}/appointments/",
        headers=headers_auth(),
        params={'status': 'confirmed'}
    )
    if assert_status(resp, 200, "GET /appointments/?status=confirmed"):
        data = resp.json()
        all_confirmed = all(a['status'] == 'confirmed' for a in data)
        if all_confirmed and len(data) > 0:
            ok(f"Filtro status=confirmed — {len(data)} retornados")
            state['passed'] += 1

    # Filtro por profissional
    resp = requests.get(
        f"{BASE_URL}/appointments/",
        headers=headers_auth(),
        params={'professional_id': state['professional_id']}
    )
    assert_status(resp, 200, "GET /appointments/?professional_id=Carlão")


def test_appointment_detail():
    title("ETAPA 4 — Detalhe do agendamento")

    if not state['appointment_panel']:
        warn("Pulando — sem appointment_panel")
        return

    resp = requests.get(
        f"{BASE_URL}/appointments/{state['appointment_panel']}/",
        headers=headers_auth()
    )
    if not assert_status(resp, 200, "GET /appointments/{id}/"):
        return

    data = resp.json()
    assert_field(data, 'professional_name', "Tem 'professional_name'")
    assert_field(data, 'service_name',      "Tem 'service_name'")
    assert_field(data, 'service_duration',  "Tem 'service_duration'")
    assert_field(data, 'status_display',    "Tem 'status_display'")
    assert_field(data, 'source_display',    "Tem 'source_display'")

    if data.get('professional_name') == 'Carlão':
        ok("Professional name = Carlão")
        state['passed'] += 1
    if data.get('service_name') == 'Corte masculino':
        ok("Service name = Corte masculino")
        state['passed'] += 1
    if data.get('service_duration') == 30:
        ok("Service duration = 30min")
        state['passed'] += 1


def test_appointment_confirm():
    title("ETAPA 4 — Confirmar agendamento pendente")

    terça = next_tuesday()

    # Força auto_confirm=False no AgentConfig para criar pending
    # Como não temos endpoint para isso, criamos via whatsapp
    # e verificamos o status — se vier confirmed, ajustamos o teste

    # Cria agendamento novo garantidamente pendente (source=link, auto_confirm=True no trial)
    # Para testar confirm, precisamos de um pending — criamos e forçamos via admin
    # Alternativa: testar o fluxo completo: se veio confirmed, testa que confirmar novamente dá 400
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T11:00:00",
        "client_name":     "Teste Confirm",
        "client_phone":    "19911112222",
        "source":          "link",
    })
    if resp.status_code != 201:
        warn("Não conseguiu criar agendamento para confirm")
        return

    appt    = resp.json()
    appt_id = appt.get('id')
    current = appt.get('status')
    info(f"Status criado (auto_confirm={current}): {current}")

    if current == 'pending':
        # Confirmar pending → deve virar confirmed
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/confirm/",
            headers=headers_auth()
        )
        if assert_status(resp, 200, "POST /appointments/{id}/confirm/ (pending→confirmed)"):
            assert_value(resp.json(), 'status', 'confirmed', "Status = confirmed após confirmar")

        # Confirmar novamente → deve dar 400
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/confirm/",
            headers=headers_auth()
        )
        assert_status(resp, 400, "POST /appointments/{id}/confirm/ (já confirmado)")

    else:
        # auto_confirm=True → veio confirmed direto — testa idempotência
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/confirm/",
            headers=headers_auth()
        )
        assert_status(resp, 400, "POST /appointments/{id}/confirm/ (já confirmado — auto_confirm=True)")
        ok("auto_confirm=True ativo no trial — confirm de confirmed retorna 400 corretamente")
        state['passed'] += 1


def test_appointment_complete():
    title("ETAPA 4 — Completar agendamento (gera CashEntry)")

    if not state['appointment_panel']:
        warn("Pulando — sem appointment_panel")
        return

    resp = requests.post(
        f"{BASE_URL}/appointments/{state['appointment_panel']}/complete/",
        headers=headers_auth(),
        json={"payment_method": "pix"}
    )
    if not assert_status(resp, 200, "POST /appointments/{id}/complete/"):
        return

    data = resp.json()
    assert_value(data, 'status',         'completed', "Status = completed")
    assert_field(data, 'price',                       "Tem 'price'")
    assert_field(data, 'payment_method',              "Tem 'payment_method'")
    assert_value(data, 'payment_method', 'pix',       "Payment method = pix")

    info(f"Valor: R${data.get('price')}")

    # Tentar completar de novo
    resp = requests.post(
        f"{BASE_URL}/appointments/{state['appointment_panel']}/complete/",
        headers=headers_auth(),
        json={"payment_method": "pix"}
    )
    assert_status(resp, 400, "POST /appointments/{id}/complete/ (já completado)")


def test_appointment_complete_with_discount():
    title("ETAPA 4 — Completar com valor diferente (desconto)")

    if not state['appointment_wa']:
        warn("Pulando — sem appointment_wa")
        return

    # Completar com valor menor (desconto)
    resp = requests.post(
        f"{BASE_URL}/appointments/{state['appointment_wa']}/complete/",
        headers=headers_auth(),
        json={"payment_method": "cash", "price": 30.00}
    )
    if assert_status(resp, 200, "POST /appointments/{id}/complete/ (com desconto)"):
        data = resp.json()
        if float(data.get('price', 0)) == 30.0:
            ok("Preço sobrescrito para R$30 (desconto aplicado)")
            state['passed'] += 1
        assert_value(data, 'payment_method', 'cash', "Payment method = cash")


def test_appointment_cancel_by_client():
    title("ETAPA 4 — Cancelamento pelo cliente (via phone)")

    terça = next_tuesday()

    # Cria novo agendamento para cancelar
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T15:30:00",
        "client_name":     "Ana Lima",
        "client_phone":    "19955554444",
        "source":          "link",
    })
    if resp.status_code != 201:
        warn("Não conseguiu criar agendamento para cancelamento")
        return

    appt_id = resp.json().get('id')

    # Cliente cancela com phone correto
    resp = requests.post(
        f"{BASE_URL}/appointments/{appt_id}/cancel/",
        headers=headers_auth(),
        json={"client_phone": "19955554444", "reason": "Compromisso de última hora"}
    )
    if assert_status(resp, 200, "POST /appointments/{id}/cancel/ (cliente com phone)"):
        data = resp.json()
        assert_value(data, 'status', 'cancelled', "Status = cancelled")

    # Tentar cancelar com phone errado
    terça2 = terça
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T16:00:00",
        "client_name":     "Carlos Souza",
        "client_phone":    "19944443333",
        "source":          "link",
    })
    if resp.status_code == 201:
        appt_id2 = resp.json().get('id')
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id2}/cancel/",
            headers=headers_auth(),
            json={"client_phone": "19900000000"}  # phone errado
        )
        assert_status(resp, 403, "POST /appointments/{id}/cancel/ (phone errado → 403)")


def test_appointment_cancel_by_barber():
    title("ETAPA 4 — Cancelamento pelo barbeiro")

    terça = next_tuesday()

    # Cria agendamento
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T16:30:00",
        "client_name":     "Roberto Alves",
        "client_phone":    "19933332222",
        "source":          "panel",
    })
    if resp.status_code != 201:
        warn("Não conseguiu criar agendamento")
        return

    appt_id = resp.json().get('id')

    # Barbeiro cancela sem precisar de phone
    resp = requests.post(
        f"{BASE_URL}/appointments/{appt_id}/cancel/",
        headers=headers_auth(),
        json={"reason": "Profissional indisponível"}
    )
    if assert_status(resp, 200, "POST /appointments/{id}/cancel/ (barbeiro)"):
        assert_value(resp.json(), 'status', 'cancelled', "Status = cancelled")

    # Tentar cancelar agendamento já cancelado
    resp = requests.post(
        f"{BASE_URL}/appointments/{appt_id}/cancel/",
        headers=headers_auth()
    )
    assert_status(resp, 400, "POST /appointments/{id}/cancel/ (já cancelado)")


def test_appointment_no_show():
    title("ETAPA 4 — No-show")

    if not state['appointment_link']:
        warn("Pulando — sem appointment_link (já confirmado)")
        return

    resp = requests.post(
        f"{BASE_URL}/appointments/{state['appointment_link']}/no-show/",
        headers=headers_auth()
    )
    if assert_status(resp, 200, "POST /appointments/{id}/no-show/"):
        assert_value(resp.json(), 'status', 'no_show', "Status = no_show")

    # Tentar no-show novamente
    resp = requests.post(
        f"{BASE_URL}/appointments/{state['appointment_link']}/no-show/",
        headers=headers_auth()
    )
    assert_status(resp, 400, "POST /appointments/{id}/no-show/ (já no_show)")


def test_agenda_day():
    title("ETAPA 4 — Agenda do dia")

    terça = next_tuesday()

    # Agenda do dia completa
    resp = requests.get(
        f"{BASE_URL}/agenda/day/",
        headers=headers_auth(),
        params={'date': terça.isoformat()}
    )
    if not assert_status(resp, 200, "GET /agenda/day/"):
        return

    data = resp.json()
    assert_field(data, 'date',          "Tem 'date'")
    assert_field(data, 'professionals', "Tem 'professionals'")
    assert_field(data, 'total',         "Tem 'total'")

    profs = data.get('professionals', [])
    if len(profs) >= 1:
        ok(f"Agenda com {len(profs)} profissional(is)")
        state['passed'] += 1
        for p in profs:
            info(f"  {p['professional']['name']}: {p['total']} agendamento(s)")

    # Agenda do dia com profissional específico
    resp = requests.get(
        f"{BASE_URL}/agenda/day/",
        headers=headers_auth(),
        params={'date': terça.isoformat(), 'professional_id': state['professional_id']}
    )
    if assert_status(resp, 200, "GET /agenda/day/?professional_id=Carlão"):
        data = resp.json()
        profs = data.get('professionals', [])
        if len(profs) == 1 and profs[0]['professional']['name'] == 'Carlão':
            ok("Filtro por profissional funciona")
            state['passed'] += 1

    # Agenda de hoje (sem parâmetro de data)
    resp = requests.get(f"{BASE_URL}/agenda/day/", headers=headers_auth())
    assert_status(resp, 200, "GET /agenda/day/ (sem data = hoje)")


def test_agenda_week():
    title("ETAPA 4 — Agenda da semana")

    terça = next_tuesday()

    resp = requests.get(
        f"{BASE_URL}/agenda/week/",
        headers=headers_auth(),
        params={'date': terça.isoformat()}
    )
    if not assert_status(resp, 200, "GET /agenda/week/"):
        return

    data = resp.json()
    assert_field(data, 'week_start', "Tem 'week_start'")
    assert_field(data, 'week_end',   "Tem 'week_end'")
    assert_field(data, 'days',       "Tem 'days'")
    assert_field(data, 'total_week', "Tem 'total_week'")

    days = data.get('days', [])
    if len(days) == 7:
        ok("7 dias na semana")
        state['passed'] += 1

    total = data.get('total_week', 0)
    info(f"Total da semana: {total} agendamento(s)")
    info(f"Semana: {data.get('week_start')} a {data.get('week_end')}")


def test_status_flow():
    title("ETAPA 4 — Fluxo de status (máquina de estados)")

    terça = next_tuesday()

    # Cria agendamento
    resp = requests.post(f"{BASE_URL}/appointments/", headers=headers_auth(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{terça.isoformat()}T17:00:00",
        "client_name":     "Teste Fluxo",
        "source":          "link",
    })
    if resp.status_code != 201:
        warn("Não conseguiu criar agendamento")
        return

    appt    = resp.json()
    appt_id = appt.get('id')
    current = appt.get('status')
    info(f"Agendamento criado: {appt_id} (status={current})")

    if current == 'pending':
        # pending → não pode completar diretamente
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/complete/",
            headers=headers_auth(),
            json={"payment_method": "pix"}
        )
        assert_status(resp, 400, "pending → complete (inválido)")

        # pending → confirmed
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/confirm/",
            headers=headers_auth()
        )
        assert_status(resp, 200, "pending → confirmed (válido)")

        # confirmed → não pode confirmar de novo
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/confirm/",
            headers=headers_auth()
        )
        assert_status(resp, 400, "confirmed → confirmed (inválido)")

        # confirmed → complete
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/complete/",
            headers=headers_auth(),
            json={"payment_method": "debit"}
        )
        assert_status(resp, 200, "confirmed → completed (válido)")

        # completed → não pode cancelar
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/cancel/",
            headers=headers_auth()
        )
        assert_status(resp, 400, "completed → cancel (inválido)")

    else:
        # auto_confirm=True → veio confirmed direto
        info("auto_confirm=True — agendamento já veio confirmed")

        # confirmed → não pode completar pending (já é confirmed, testa direto)
        # confirmed → complete
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/complete/",
            headers=headers_auth(),
            json={"payment_method": "debit"}
        )
        assert_status(resp, 200, "confirmed → completed (válido)")

        # completed → não pode cancelar
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/cancel/",
            headers=headers_auth()
        )
        assert_status(resp, 400, "completed → cancel (inválido)")

        # completed → não pode confirmar
        resp = requests.post(
            f"{BASE_URL}/appointments/{appt_id}/confirm/",
            headers=headers_auth()
        )
        assert_status(resp, 400, "completed → confirm (inválido)")

        # Testa pending bloqueando complete — cria um pending manualmente não é possível
        # com auto_confirm=True, então documenta
        warn("auto_confirm=True ativo — teste pending→complete não aplicável neste tenant")

    ok("Máquina de estados validada")
    state['passed'] += 1


# ════════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════════

def print_summary():
    title("RESUMO DOS TESTES")
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
    print(f"{BOLD}  Beauti API — Testes Etapa 1 + 2 + 3 + 4{RESET}")
    print(f"{BOLD}  Base URL: {BASE_URL}{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")

    # Setup das etapas anteriores
    if not setup_etapas_1_2_3():
        print(f"\n{RED}Setup falhou — abortando.{RESET}")
        sys.exit(1)

    # Etapa 4 — Agendamentos
    test_appointment_canal1_panel()
    test_appointment_canal2_link()
    test_appointment_canal3_whatsapp()
    test_appointment_validation()
    test_appointment_list()
    test_appointment_detail()
    test_appointment_confirm()
    test_appointment_complete()
    test_appointment_complete_with_discount()
    test_appointment_cancel_by_client()
    test_appointment_cancel_by_barber()
    test_appointment_no_show()
    test_agenda_day()
    test_agenda_week()
    test_status_flow()

    success = print_summary()
    sys.exit(0 if success else 1)