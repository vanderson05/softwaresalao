"""
test_m3.py — Testes do M3: Perfil público + Auth cliente + Pacotes

Uso:
    python test_m3.py

Requisitos:
    pip install requests PyJWT
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
    'email':        f"m3_{datetime.now().strftime('%H%M%S')}@beauti.com",
    'password':     'Senha@123',
    'owner_token':  None,
    'client_token': None,
    'slug':         None,
    'service_id':   None,
    'package_id':   None,
    'appointment_id': None,
    # Telefone único por execução — garante is_new_client=True
    'client_phone': f"199{datetime.now().strftime('%H%M%S%f')[:8]}",
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

def owner_headers():
    return {'Authorization': f"Bearer {state['owner_token']}", 'Content-Type': 'application/json'}

def client_headers():
    return {'Authorization': f"ClientBearer {state['client_token']}", 'Content-Type': 'application/json'}


# ════════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════════

def setup():
    title("SETUP — Criando tenant para testes M3")

    resp = requests.post(f"{API_URL}/auth/register/", json={
        "business_name": "Barbearia M3 Test",
        "phone": "19999999999",
        "email": state['email'],
        "password": state['password'],
        "type": "barbershop",
    })
    if resp.status_code != 201:
        fail(f"Registro falhou"); return False
    state['slug'] = resp.json()['tenant']['slug']
    ok(f"Tenant criado: {state['slug']}")

    resp = requests.post(f"{API_URL}/auth/login/", json={"email": state['email'], "password": state['password']})
    state['owner_token'] = resp.json()['tokens']['access']
    ok("Login owner OK")

    h = owner_headers()

    # Estabelecimento completo
    requests.patch(f"{API_URL}/setup/establishment/", headers=h, json={
        "address": "Rua das Flores, 100", "city": "Americana",
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

    resp = requests.post(f"{API_URL}/professionals/", headers=h, json={"name": "Carlão", "commission_pct": 40, "slot_interval": 30})
    prof_id = resp.json()['id']

    resp = requests.post(f"{API_URL}/services/", headers=h, json={"name": "Corte masculino", "duration_min": 30, "price": 35.00})
    state['service_id'] = resp.json()['id']

    requests.post(f"{API_URL}/schedules/bulk/", headers=h, json={
        "professional_id": prof_id,
        "schedules": [
            {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 2, "start_time": "09:00", "end_time": "18:00"},
            {"weekday": 3, "start_time": "09:00", "end_time": "18:00"},
        ]
    })

    requests.post(f"{API_URL}/setup/complete/", headers=h)
    ok(f"Setup completo — slug={state['slug']}, service={state['service_id']}")
    return True


# ════════════════════════════════════════════════════════════════
# TESTES PÚBLICOS — sem autenticação
# ════════════════════════════════════════════════════════════════

def test_home_public():
    title("M3 — Home pública (lista barbearias)")

    resp = requests.get(f"{BASE_URL}/b/")
    assert_status(resp, 200, "GET /b/")
    data = resp.json()
    assert_ok('results' in data, "Tem 'results'")
    assert_ok('total' in data,   "Tem 'total'")
    assert_ok(data['total'] >= 1, f"Pelo menos 1 barbearia ({data.get('total')})")

    # Busca por nome
    resp = requests.get(f"{BASE_URL}/b/", params={'q': 'M3'})
    assert_status(resp, 200, "GET /b/?q=M3")
    data = resp.json()
    assert_ok(data['total'] >= 1, "Busca por nome encontrou resultados")

    # Busca por cidade
    resp = requests.get(f"{BASE_URL}/b/", params={'city': 'Americana'})
    assert_status(resp, 200, "GET /b/?city=Americana")


def test_profile_public():
    title("M3 — Perfil público da barbearia")
    slug = state['slug']

    resp = requests.get(f"{BASE_URL}/b/{slug}/")
    if not assert_status(resp, 200, f"GET /b/{slug}/"):
        return
    data = resp.json()
    assert_ok('slug' in data,           "Tem 'slug'")
    assert_ok('name' in data,           "Tem 'name'")
    assert_ok('address' in data,        "Tem 'address'")
    assert_ok('business_hours' in data, "Tem 'business_hours'")
    assert_ok(len(data['business_hours']) == 7, "7 dias de horário")
    info(f"Barbearia: {data['name']} — {data['city']}")

    # Barbearia inexistente
    resp = requests.get(f"{BASE_URL}/b/barbearia-que-nao-existe/")
    assert_status(resp, 404, "GET /b/slug-invalido/ → 404")


def test_services_public():
    title("M3 — Serviços públicos")
    slug = state['slug']

    resp = requests.get(f"{BASE_URL}/b/{slug}/services/")
    if not assert_status(resp, 200, f"GET /b/{slug}/services/"):
        return
    data = resp.json()
    assert_ok(len(data) >= 1, f"{len(data)} serviço(s) retornado(s)")
    assert_ok('id' in data[0],           "Serviço tem 'id'")
    assert_ok('price' in data[0],        "Serviço tem 'price'")
    assert_ok('duration_min' in data[0], "Serviço tem 'duration_min'")


def test_professionals_public():
    title("M3 — Profissionais públicos")
    slug = state['slug']

    resp = requests.get(f"{BASE_URL}/b/{slug}/professionals/")
    if not assert_status(resp, 200, f"GET /b/{slug}/professionals/"):
        return
    data = resp.json()
    assert_ok(len(data) >= 1, f"{len(data)} profissional(is) retornado(s)")
    assert_ok('name' in data[0], "Profissional tem 'name'")


# ════════════════════════════════════════════════════════════════
# AUTH CLIENTE FINAL
# ════════════════════════════════════════════════════════════════

def test_client_auth():
    title("M3 — Auth cliente: código via WhatsApp")
    slug  = state['slug']
    phone = state['client_phone']

    # Solicita código
    resp = requests.post(f"{BASE_URL}/b/{slug}/auth/request-code/", json={"phone": phone})
    if not assert_status(resp, 200, "POST /b/{slug}/auth/request-code/"):
        return
    data = resp.json()
    assert_ok('message' in data,          "Tem 'message'")
    assert_ok(data.get('expires_in_minutes') == 10, "Expira em 10 minutos")

    # Busca o código do banco (DEV — em prod viria via WhatsApp)
    from clients.models import ClientOTP
    from tenants.models import Tenant
    tenant = Tenant.objects.get(slug=slug)
    otp    = ClientOTP.objects.filter(tenant=tenant, phone=phone, used=False).first()

    if not otp:
        warn("OTP não encontrado no banco — pulando verificação")
        return

    code = otp.code
    info(f"Código OTP (DEV): {code}")

    # Verifica código correto
    resp = requests.post(f"{BASE_URL}/b/{slug}/auth/verify-code/", json={"phone": phone, "code": code})
    if not assert_status(resp, 200, "POST /b/{slug}/auth/verify-code/ (código correto)"):
        return
    data = resp.json()
    assert_ok('token' in data,        "Tem 'token' JWT")
    assert_ok('is_new_client' in data, "Tem 'is_new_client'")
    assert_ok('client' in data,        "Tem 'client'")
    assert_ok(data['is_new_client'] is True, "is_new_client = True (primeiro acesso)")

    state['client_token'] = data['token']
    info(f"Cliente autenticado: {data['client']['phone']}")

    # Verifica código inválido
    resp = requests.post(f"{BASE_URL}/b/{slug}/auth/verify-code/", json={"phone": phone, "code": "000000"})
    assert_status(resp, 400, "POST /b/{slug}/auth/verify-code/ (código errado → 400)")

    # Segundo login — mesmo cliente, is_new_client = False
    resp = requests.post(f"{BASE_URL}/b/{slug}/auth/request-code/", json={"phone": phone})
    otp2 = ClientOTP.objects.filter(tenant=tenant, phone=phone, used=False).first()
    if otp2:
        resp = requests.post(f"{BASE_URL}/b/{slug}/auth/verify-code/", json={"phone": phone, "code": otp2.code})
        if resp.status_code == 200:
            data2 = resp.json()
            assert_ok(data2.get('is_new_client') is False, "Segundo login: is_new_client = False")
            state['client_token'] = data2['token']


def test_client_update_name():
    title("M3 — Cliente atualiza nome (primeiro acesso)")
    slug = state['slug']

    if not state['client_token']:
        warn("Pulando — sem client_token")
        return

    resp = requests.patch(
        f"{BASE_URL}/b/{slug}/me/",
        headers=client_headers(),
        json={"name": "João Silva"}
    )
    if assert_status(resp, 200, "PATCH /b/{slug}/me/"):
        data = resp.json()
        assert_ok(data['client']['name'] == 'João Silva', "Nome atualizado para João Silva")


# ════════════════════════════════════════════════════════════════
# SLOTS E AGENDAMENTO
# ════════════════════════════════════════════════════════════════

def test_slots_requires_auth():
    title("M3 — Slots exige autenticação")
    slug = state['slug']

    resp = requests.get(f"{BASE_URL}/b/{slug}/slots/", params={
        'service_id': state['service_id'],
        'date': (date.today() + timedelta(days=2)).isoformat()
    })
    assert_status(resp, 401, "GET /b/{slug}/slots/ sem auth → 401")


def test_slots_authenticated():
    title("M3 — Slots com cliente autenticado")
    slug = state['slug']

    if not state['client_token']:
        warn("Pulando — sem client_token")
        return

    for i in range(1, 8):
        d = date.today() + timedelta(days=i)
        if d.weekday() in (1, 2, 3):
            check_date = d
            break
    else:
        check_date = date.today() + timedelta(days=2)

    resp = requests.get(
        f"{BASE_URL}/b/{slug}/slots/",
        headers=client_headers(),
        params={'service_id': state['service_id'], 'date': check_date.isoformat()}
    )
    if assert_status(resp, 200, "GET /b/{slug}/slots/ (autenticado)"):
        data = resp.json()
        assert_ok('slots' in data, "Tem 'slots'")
        info(f"Slots disponíveis em {check_date}: {len(data.get('slots', []))}")


def test_book():
    title("M3 — Agendar pelo link público")
    slug = state['slug']

    if not state['client_token']:
        warn("Pulando — sem client_token")
        return

    # Busca próximo slot disponível
    resp = requests.get(f"{BASE_URL}/b/{slug}/slots/", headers=client_headers(), params={
        'service_id': state['service_id'],
        'date': (date.today() + timedelta(days=2)).isoformat()
    })

    slots = []
    if resp.status_code == 200:
        slots = resp.json().get('slots', [])

    if not slots:
        # Tenta próximos dias
        for i in range(1, 8):
            d = date.today() + timedelta(days=i)
            if d.weekday() in (1, 2, 3):
                r = requests.get(f"{BASE_URL}/b/{slug}/slots/", headers=client_headers(),
                    params={'service_id': state['service_id'], 'date': d.isoformat()})
                if r.status_code == 200:
                    slots = r.json().get('slots', [])
                    if slots:
                        break

    if not slots:
        warn("Nenhum slot disponível — pulando teste de agendamento")
        return

    first_slot = slots[0]
    starts_at  = first_slot['datetime']

    resp = requests.post(f"{BASE_URL}/b/{slug}/book/", headers=client_headers(), json={
        "professional_id": first_slot['professional']['id'],
        "service_id":      state['service_id'],
        "starts_at":       starts_at,
        "client_name":     "João Silva",
    })

    if assert_status(resp, 201, "POST /b/{slug}/book/"):
        data = resp.json()
        assert_ok('appointment' in data,           "Tem 'appointment'")
        assert_ok(data['appointment']['status'] in ('pending', 'confirmed'), "Status válido")
        assert_ok('address' in data['appointment'], "Tem 'address'")
        state['appointment_id'] = data['appointment']['id']
        info(f"Agendado: {data['appointment']['service']} às {data['appointment']['starts_at'][:16]}")


def test_my_appointments():
    title("M3 — Meus agendamentos")
    slug = state['slug']

    if not state['client_token']:
        warn("Pulando — sem client_token")
        return

    resp = requests.get(f"{BASE_URL}/b/{slug}/my-appointments/", headers=client_headers())
    if assert_status(resp, 200, "GET /b/{slug}/my-appointments/"):
        data = resp.json()
        assert_ok('upcoming' in data, "Tem 'upcoming'")
        assert_ok('past' in data,     "Tem 'past'")
        total = len(data['upcoming']) + len(data['past'])
        info(f"Próximos: {len(data['upcoming'])} | Histórico: {len(data['past'])}")
        if total > 0:
            ok(f"{total} agendamento(s) encontrado(s)")
            state['passed'] += 1


def test_cancel_my_appointment():
    title("M3 — Cancelar meu agendamento")
    slug = state['slug']

    if not state['client_token'] or not state['appointment_id']:
        warn("Pulando — sem client_token ou appointment_id")
        return

    resp = requests.post(
        f"{BASE_URL}/b/{slug}/my-appointments/{state['appointment_id']}/cancel/",
        headers=client_headers()
    )
    if assert_status(resp, 200, "POST /b/{slug}/my-appointments/{id}/cancel/"):
        assert_ok(resp.json().get('status') == 'cancelled', "Status = cancelled")


# ════════════════════════════════════════════════════════════════
# PACOTES
# ════════════════════════════════════════════════════════════════

def test_packages_owner():
    title("M3 — Pacotes (gestão pelo owner)")

    # Criar pacote
    resp = requests.post(f"{API_URL}/packages/", headers=owner_headers(), json={
        "service_id":  state['service_id'],
        "name":        "Pacote Mensal Corte",
        "description": "4 cortes com 14% de desconto",
        "sessions":    4,
        "price":       120.00,
    })
    if assert_status(resp, 201, "POST /api/packages/"):
        data = resp.json()
        state['package_id'] = data['id']
        assert_ok('discount_pct' in data,      "Tem 'discount_pct'")
        assert_ok(data['discount_pct'] > 0,    f"Desconto calculado: {data['discount_pct']}%")
        assert_ok('price_per_session' in data, "Tem 'price_per_session'")
        info(f"Pacote: {data['name']} — {data['sessions']}x R${data['price_per_session']}/sessão ({data['discount_pct']}% off)")

    # Listar pacotes
    resp = requests.get(f"{API_URL}/packages/", headers=owner_headers())
    if assert_status(resp, 200, "GET /api/packages/"):
        assert_ok(len(resp.json()) >= 1, "Pelo menos 1 pacote")

    # Atribuir pacote a cliente
    if state['package_id']:
        resp = requests.post(f"{API_URL}/packages/assign/", headers=owner_headers(), json={
            "package_id":   state['package_id'],
            "client_phone": state['client_phone'],
            "client_name":  "João Silva",
        })
        if assert_status(resp, 201, "POST /api/packages/assign/"):
            data = resp.json()
            assert_ok('sessions_remaining' in data, "Tem 'sessions_remaining'")
            assert_ok(data['sessions_remaining'] == 4, "4 sessões restantes após compra")
            info(f"Pacote atribuído: {data['sessions_remaining']} sessões disponíveis")

    # Listar pacotes dos clientes
    resp = requests.get(f"{API_URL}/packages/clients/", headers=owner_headers())
    assert_status(resp, 200, "GET /api/packages/clients/")


def test_packages_public():
    title("M3 — Pacotes públicos na vitrine")
    slug = state['slug']

    resp = requests.get(f"{BASE_URL}/b/{slug}/packages/")
    if assert_status(resp, 200, f"GET /b/{slug}/packages/"):
        data = resp.json()
        if len(data) >= 1:
            ok(f"{len(data)} pacote(s) na vitrine")
            state['passed'] += 1
            p = data[0]
            assert_ok('discount_pct' in p,      "Pacote público tem 'discount_pct'")
            assert_ok('original_price' in p,    "Pacote público tem 'original_price'")


# ════════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════════

def print_summary():
    title("RESUMO DOS TESTES M3")
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
    print(f"{BOLD}  Beauti — Testes M3: Perfil público + Auth + Pacotes{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")

    if not setup():
        print(f"\n{RED}Setup falhou.{RESET}")
        sys.exit(1)

    # Públicos
    test_home_public()
    test_profile_public()
    test_services_public()
    test_professionals_public()

    # Auth cliente
    test_client_auth()
    test_client_update_name()

    # Slots e agendamento
    test_slots_requires_auth()
    test_slots_authenticated()
    test_book()
    test_my_appointments()
    test_cancel_my_appointment()

    # Pacotes
    test_packages_owner()
    test_packages_public()

    success = print_summary()
    sys.exit(0 if success else 1)