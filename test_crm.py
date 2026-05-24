"""
test_crm.py — Testes do CRM: Clientes, Insights e Assinaturas

Uso:
    python test_crm.py
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

BASE_URL = "http://127.0.0.1:8000"
API_URL  = f"{BASE_URL}/api"

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
    'email':           f"crm_{datetime.now().strftime('%H%M%S')}@beauti.com",
    'password':        'Senha@123',
    'owner_token':     None,
    'slug':            None,
    'service_id':      None,
    'professional_id': None,
    'client_id':       None,
    'subscription_id': None,
    'client_phone':    f"199{datetime.now().strftime('%H%M%S%f')[:8]}",
    'errors':          [],
    'passed':          0,
    'failed':          0,
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

def assert_status(resp, expected, test_name):
    if resp.status_code == expected:
        ok(f"{test_name} — status {resp.status_code}")
        state['passed'] += 1
        return True
    fail(f"{test_name} — esperado {expected}, recebeu {resp.status_code}")
    try:
        info(f"Resposta: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:300]}")
    except Exception:
        info(f"Resposta: {resp.text[:200]}")
    state['failed'] += 1
    state['errors'].append(test_name)
    return False

def h():
    return {'Authorization': f"Bearer {state['owner_token']}", 'Content-Type': 'application/json'}


# ════════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════════

def setup():
    title("SETUP — Criando tenant + agendamentos para popular CRM")

    # Registro + login
    resp = requests.post(f"{API_URL}/auth/register/", json={
        "business_name": "Barbearia CRM Test",
        "phone": "19999999999",
        "email": state['email'],
        "password": state['password'],
        "type": "barbershop",
    })
    if resp.status_code != 201:
        fail("Registro falhou"); return False

    resp = requests.post(f"{API_URL}/auth/login/", json={"email": state['email'], "password": state['password']})
    state['owner_token'] = resp.json()['tokens']['access']
    state['slug']        = resp.json()['tenant']['slug']
    ok(f"Tenant: {state['slug']}")

    # Setup completo
    requests.patch(f"{API_URL}/setup/establishment/", headers=h(), json={
        "address": "Rua CRM, 42", "city": "Americana",
        "business_hours": [
            {"weekday": i, "open_time": "09:00", "close_time": "18:00"}
            for i in range(6)
        ] + [{"weekday": 6, "is_closed": True}]
    })

    resp = requests.post(f"{API_URL}/professionals/", headers=h(), json={"name": "Carlão", "slot_interval": 30})
    state['professional_id'] = resp.json()['id']

    resp = requests.post(f"{API_URL}/services/", headers=h(), json={"name": "Corte", "duration_min": 30, "price": 35.00})
    state['service_id'] = resp.json()['id']

    requests.post(f"{API_URL}/schedules/bulk/", headers=h(), json={
        "professional_id": state['professional_id'],
        "schedules": [{"weekday": i, "start_time": "09:00", "end_time": "18:00"} for i in range(5)]
    })
    requests.post(f"{API_URL}/setup/complete/", headers=h())

    # Cria agendamentos para popular o CRM
    for i in range(1, 8):
        d = date.today() + timedelta(days=i)
        if d.weekday() < 5:
            check_date = d; break

    phones = [state['client_phone'], f"199{datetime.now().strftime('%f')[:8]}"]
    names  = ["João Silva", "Maria Santos"]

    for idx, (phone, name) in enumerate(zip(phones, names)):
        resp = requests.post(f"{API_URL}/appointments/", headers=h(), json={
            "professional_id": state['professional_id'],
            "service_id":      state['service_id'],
            "starts_at":       f"{check_date.isoformat()}T{9+idx}:00:00",
            "client_name":     name,
            "client_phone":    phone,
            "source":          "panel",
        })
        if resp.status_code == 201:
            appt_id = resp.json()['id']
            # Completa para gerar histórico
            requests.post(f"{API_URL}/appointments/{appt_id}/complete/", headers=h(), json={"payment_method": "pix"})

    # Salva client_id do primeiro cliente
    from clients.models import Client
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'softwaresalao.settings')
    django.setup()
    try:
        client = Client.objects.get(phone=state['client_phone'])
        state['client_id'] = str(client.id)
    except Exception:
        pass

    ok(f"Setup completo — client_id: {state['client_id']}")
    return True


# ════════════════════════════════════════════════════════════════
# TESTES CRM
# ════════════════════════════════════════════════════════════════

def test_clients_list():
    title("CRM — Listagem de clientes")

    resp = requests.get(f"{API_URL}/crm/clients/", headers=h())
    if not assert_status(resp, 200, "GET /api/crm/clients/"):
        return
    data = resp.json()
    assert_ok('clients' in data, "Tem 'clients'")
    assert_ok('total' in data,   "Tem 'total'")
    assert_ok(data['total'] >= 1, f"{data['total']} cliente(s) encontrado(s)")

    if data['clients']:
        c = data['clients'][0]
        assert_ok('client_id' in c,    "Tem 'client_id'")
        assert_ok('name' in c,         "Tem 'name'")
        assert_ok('phone' in c,        "Tem 'phone'")
        assert_ok('total_visits' in c, "Tem 'total_visits'")
        assert_ok('total_spent' in c,  "Tem 'total_spent'")
        assert_ok('last_visit_at' in c,"Tem 'last_visit_at'")

    # Busca por nome
    resp = requests.get(f"{API_URL}/crm/clients/", headers=h(), params={'q': 'João'})
    assert_status(resp, 200, "GET /crm/clients/?q=João")

    # Ordenação por visitas
    resp = requests.get(f"{API_URL}/crm/clients/", headers=h(), params={'order': 'total_visits'})
    assert_status(resp, 200, "GET /crm/clients/?order=total_visits")


def test_client_detail():
    title("CRM — Perfil completo do cliente")

    if not state['client_id']:
        warn("Pulando — sem client_id")
        return

    resp = requests.get(f"{API_URL}/crm/clients/{state['client_id']}/", headers=h())
    if not assert_status(resp, 200, "GET /crm/clients/{id}/"):
        return

    data = resp.json()
    assert_ok('client' in data,       "Tem 'client'")
    assert_ok('profile' in data,      "Tem 'profile'")
    assert_ok('appointments' in data, "Tem 'appointments'")
    assert_ok('packages' in data,     "Tem 'packages'")
    assert_ok('subscription' in data, "Tem 'subscription'")

    profile = data['profile']
    assert_ok('total_visits' in profile,  "Profile tem 'total_visits'")
    assert_ok('total_spent' in profile,   "Profile tem 'total_spent'")
    assert_ok('last_visit_at' in profile, "Profile tem 'last_visit_at'")

    info(f"Cliente: {data['client']['name']} — {profile['total_visits']} visitas — R${profile['total_spent']}")

    # Atualiza notas e aniversário
    resp = requests.patch(f"{API_URL}/crm/clients/{state['client_id']}/", headers=h(), json={
        "notes":     "Cliente VIP, prefere Carlão",
        "birthdate": "1990-05-15",
    })
    assert_status(resp, 200, "PATCH /crm/clients/{id}/ (notas + aniversário)")


def test_insight_summary():
    title("CRM — Resumo geral")

    resp = requests.get(f"{API_URL}/crm/insights/summary/", headers=h())
    if not assert_status(resp, 200, "GET /crm/insights/summary/"):
        return

    data = resp.json()
    assert_ok('total_clients' in data,     "Tem 'total_clients'")
    assert_ok('new_this_month' in data,    "Tem 'new_this_month'")
    assert_ok('active_last_30d' in data,   "Tem 'active_last_30d'")
    assert_ok('inactive_over_30d' in data, "Tem 'inactive_over_30d'")
    assert_ok('birthdays_this_week' in data,"Tem 'birthdays_this_week'")
    assert_ok('active_subscriptions' in data,"Tem 'active_subscriptions'")

    info(f"Total: {data['total_clients']} | Ativos: {data['active_last_30d']} | Inativos: {data['inactive_over_30d']}")


def test_insight_inactive():
    title("CRM — Clientes inativos")

    # Padrão 30 dias
    resp = requests.get(f"{API_URL}/crm/insights/inactive/", headers=h())
    assert_status(resp, 200, "GET /crm/insights/inactive/ (30 dias padrão)")

    # Configurável — 7 dias
    resp = requests.get(f"{API_URL}/crm/insights/inactive/", headers=h(), params={'days': 7})
    if assert_status(resp, 200, "GET /crm/insights/inactive/?days=7"):
        data = resp.json()
        assert_ok(data['inactive_since_days'] == 7, "Filtro de 7 dias aplicado")
        assert_ok('clients' in data, "Tem 'clients'")

    # Configurável — 60 dias
    resp = requests.get(f"{API_URL}/crm/insights/inactive/", headers=h(), params={'days': 60})
    assert_status(resp, 200, "GET /crm/insights/inactive/?days=60")


def test_insight_birthdays():
    title("CRM — Aniversariantes da semana")

    resp = requests.get(f"{API_URL}/crm/insights/birthdays/", headers=h())
    if not assert_status(resp, 200, "GET /crm/insights/birthdays/"):
        return

    data = resp.json()
    assert_ok('period' in data,  "Tem 'period'")
    assert_ok('total' in data,   "Tem 'total'")
    assert_ok('clients' in data, "Tem 'clients'")
    info(f"Aniversariantes desta semana: {data['total']}")

    if data['clients']:
        c = data['clients'][0]
        assert_ok('days_until' in c,  "Tem 'days_until'")
        assert_ok('is_today' in c,    "Tem 'is_today'")
        assert_ok('birthdate' in c,   "Tem 'birthdate'")


def test_insight_top():
    title("CRM — Top clientes")

    # Por valor gasto
    resp = requests.get(f"{API_URL}/crm/insights/top/", headers=h())
    if not assert_status(resp, 200, "GET /crm/insights/top/ (por valor)"):
        return
    data = resp.json()
    assert_ok('clients' in data,   "Tem 'clients'")
    assert_ok(data['order'] == 'spent', "Order = spent (padrão)")

    # Por visitas
    resp = requests.get(f"{API_URL}/crm/insights/top/", headers=h(), params={'order': 'visits', 'limit': 5})
    if assert_status(resp, 200, "GET /crm/insights/top/?order=visits&limit=5"):
        data = resp.json()
        assert_ok(data['order'] == 'visits', "Order = visits")
        assert_ok(len(data['clients']) <= 5,  "Limit 5 aplicado")


def test_insight_new():
    title("CRM — Clientes novos")

    resp = requests.get(f"{API_URL}/crm/insights/new/", headers=h())
    if not assert_status(resp, 200, "GET /crm/insights/new/ (30 dias)"):
        return
    data = resp.json()
    assert_ok('clients' in data,    "Tem 'clients'")
    assert_ok(data['total'] >= 1,   f"{data['total']} cliente(s) novo(s) nos últimos 30 dias")

    # Configurável
    resp = requests.get(f"{API_URL}/crm/insights/new/", headers=h(), params={'days': 7})
    assert_status(resp, 200, "GET /crm/insights/new/?days=7")


def test_subscriptions():
    title("CRM — Assinaturas")

    # Criar assinatura limitada
    resp = requests.post(f"{API_URL}/crm/subscriptions/", headers=h(), json={
        "client_phone":    state['client_phone'],
        "client_name":     "João Silva",
        "name":            "Plano Mensal 4x",
        "type":            "limited",
        "visits_per_month": 4,
        "price":           120.00,
        "active_from":     date.today().isoformat(),
        "active_until":    (date.today() + timedelta(days=30)).isoformat(),
    })
    if assert_status(resp, 201, "POST /crm/subscriptions/ (limited)"):
        data = resp.json()
        state['subscription_id'] = data['id']
        assert_ok('visits_per_month' in data, "Tem 'visits_per_month'")
        assert_ok(data['visits_per_month'] == 4, "4 visitas/mês")
        info(f"Assinatura criada: {data['name']} — R${data['price']}/mês")

    # Criar assinatura ilimitada
    phone2 = f"198{datetime.now().strftime('%f')[:8]}"
    resp = requests.post(f"{API_URL}/crm/subscriptions/", headers=h(), json={
        "client_phone": phone2,
        "client_name":  "Maria Santos",
        "name":         "Plano VIP Ilimitado",
        "type":         "unlimited",
        "price":        199.00,
        "active_from":  date.today().isoformat(),
    })
    assert_status(resp, 201, "POST /crm/subscriptions/ (unlimited)")

    # Listar assinaturas
    resp = requests.get(f"{API_URL}/crm/subscriptions/", headers=h())
    if assert_status(resp, 200, "GET /crm/subscriptions/"):
        data = resp.json()
        assert_ok(len(data) >= 2, f"{len(data)} assinatura(s) ativa(s)")

    if not state['subscription_id']:
        return

    # Detalhe
    resp = requests.get(f"{API_URL}/crm/subscriptions/{state['subscription_id']}/", headers=h())
    if assert_status(resp, 200, "GET /crm/subscriptions/{id}/"):
        data = resp.json()
        assert_ok('visits_remaining' in data, "Tem 'visits_remaining'")
        assert_ok('can_visit' in data,        "Tem 'can_visit'")
        assert_ok(data['can_visit'] is True,  "can_visit = True (assinatura ativa)")
        assert_ok(data['visits_remaining'] == 4, "4 visitas restantes")

    # Atualizar
    resp = requests.patch(
        f"{API_URL}/crm/subscriptions/{state['subscription_id']}/",
        headers=h(),
        json={"notes": "Cliente pagou em dinheiro"}
    )
    assert_status(resp, 200, "PATCH /crm/subscriptions/{id}/")

    # Renovar
    new_until = (date.today() + timedelta(days=60)).isoformat()
    resp = requests.post(
        f"{API_URL}/crm/subscriptions/{state['subscription_id']}/renew/",
        headers=h(),
        json={"active_until": new_until}
    )
    if assert_status(resp, 200, "POST /crm/subscriptions/{id}/renew/"):
        data = resp.json()
        assert_ok(data['active_until'] == new_until, "active_until atualizado")
        assert_ok(data['visits_used'] == 0, "Visitas resetadas após renovação")

    # Cancelar
    resp = requests.delete(
        f"{API_URL}/crm/subscriptions/{state['subscription_id']}/",
        headers=h()
    )
    assert_status(resp, 200, "DELETE /crm/subscriptions/{id}/ (cancelar)")


def test_subscription_in_client_detail():
    title("CRM — Assinatura aparece no perfil do cliente")

    if not state['client_id']:
        warn("Pulando — sem client_id")
        return

    # Cria nova assinatura para o cliente (a anterior foi cancelada)
    resp = requests.post(f"{API_URL}/crm/subscriptions/", headers=h(), json={
        "client_phone":     state['client_phone'],
        "name":             "Plano Básico",
        "type":             "limited",
        "visits_per_month": 2,
        "price":            79.00,
        "active_from":      date.today().isoformat(),
    })

    # Verifica no perfil
    resp = requests.get(f"{API_URL}/crm/clients/{state['client_id']}/", headers=h())
    if resp.status_code == 200:
        data = resp.json()
        assert_ok(data.get('subscription') is not None, "Assinatura aparece no perfil do cliente")


# ════════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════════

def print_summary():
    title("RESUMO DOS TESTES CRM")
    total = state['passed'] + state['failed']
    print(f"\n  Total:    {total}")
    print(f"  {GREEN}Passou:   {state['passed']}{RESET}")
    print(f"  {RED}Falhou:   {state['failed']}{RESET}")
    if state['errors']:
        print(f"\n  {RED}Falhas:{RESET}")
        for e in state['errors']:
            print(f"    {RED}• {e}{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}Todos os testes passaram! ✓{RESET}")
    print()
    return state['failed'] == 0


if __name__ == '__main__':
    import django, os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'softwaresalao.settings')
    django.setup()

    print(f"\n{BOLD}{'═'*50}{RESET}")
    print(f"{BOLD}  Beauti — Testes CRM: Clientes + Insights + Assinaturas{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")

    if not setup():
        print(f"\n{RED}Setup falhou.{RESET}")
        sys.exit(1)

    test_clients_list()
    test_client_detail()
    test_insight_summary()
    test_insight_inactive()
    test_insight_birthdays()
    test_insight_top()
    test_insight_new()
    test_subscriptions()
    test_subscription_in_client_detail()

    success = print_summary()
    sys.exit(0 if success else 1)