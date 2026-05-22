"""
test_api.py — Testes automatizados Beauti
Etapa 1 (Auth) + Etapa 2 (Trial)

Uso:
    python test_api.py

Requisitos:
    pip install requests
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# Cores para output no terminal
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


# ── Estado compartilhado entre testes ────────────────────────────────────────
state = {
    'email':         f"teste_{datetime.now().strftime('%H%M%S')}@beauti.com",
    'password':      'Senha@123',
    'access_token':  None,
    'refresh_token': None,
    'tenant_slug':   None,
    'verify_token':  None,
    'errors':        [],
    'passed':        0,
    'failed':        0,
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
            info(f"Resposta: {resp.text[:200]}")
        state['failed'] += 1
        state['errors'].append(test_name)
        return False


def assert_field(data, field, test_name):
    if field in data:
        ok(f"{test_name} — campo '{field}' presente")
        state['passed'] += 1
        return True
    else:
        fail(f"{test_name} — campo '{field}' ausente")
        state['failed'] += 1
        state['errors'].append(test_name)
        return False


def headers_auth():
    return {
        'Authorization': f"Bearer {state['access_token']}",
        'Content-Type':  'application/json',
    }


# ════════════════════════════════════════════════════════════════
# ETAPA 1 — AUTH
# ════════════════════════════════════════════════════════════════

def test_register():
    title("ETAPA 1 — Cadastro")
    info(f"E-mail: {state['email']}")

    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "business_name": "Barbearia Teste Auto",
        "phone":         "19999999999",
        "email":         state['email'],
        "password":      state['password'],
        "type":          "barbershop",
    })

    if not assert_status(resp, 201, "POST /auth/register/"):
        return False

    data = resp.json()
    assert_field(data, 'message',   "Resposta tem 'message'")
    assert_field(data, 'tenant',    "Resposta tem 'tenant'")

    tenant = data.get('tenant', {})
    assert_field(tenant, 'slug',                "Tenant tem 'slug'")
    assert_field(tenant, 'trial_days_remaining', "Tenant tem 'trial_days_remaining'")

    if tenant.get('plan') == 'trial':
        ok("Plano é 'trial'")
        state['passed'] += 1
    else:
        fail(f"Plano deveria ser 'trial', recebeu '{tenant.get('plan')}'")
        state['failed'] += 1

    if tenant.get('trial_days_remaining', 0) >= 13:
        ok(f"Trial com {tenant['trial_days_remaining']} dias restantes")
        state['passed'] += 1
    else:
        warn(f"Trial com poucos dias: {tenant.get('trial_days_remaining')}")

    state['tenant_slug'] = tenant.get('slug')
    info(f"Slug gerado: {state['tenant_slug']}")
    return True


def test_register_duplicate_email():
    title("Validação — E-mail duplicado")

    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "business_name": "Outra Barbearia",
        "phone":         "19988888888",
        "email":         state['email'],  # mesmo e-mail
        "password":      state['password'],
    })

    assert_status(resp, 400, "POST /auth/register/ (e-mail duplicado)")

    data = resp.json()
    if 'email' in data and 'já está cadastrado' in str(data['email']):
        ok("Mensagem de erro correta para e-mail duplicado")
        state['passed'] += 1
    else:
        fail("Mensagem de erro inesperada")
        info(f"Resposta: {data}")
        state['failed'] += 1


def test_register_invalid_password():
    title("Validação — Senha fraca")

    resp = requests.post(f"{BASE_URL}/auth/register/", json={
        "business_name": "Barbearia X",
        "phone":         "19977777777",
        "email":         f"fraca_{datetime.now().strftime('%H%M%S')}@teste.com",
        "password":      "123",  # senha fraca
    })

    assert_status(resp, 400, "POST /auth/register/ (senha fraca)")


def test_login():
    title("ETAPA 1 — Login")

    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "email":    state['email'],
        "password": state['password'],
    })

    if not assert_status(resp, 200, "POST /auth/login/"):
        return False

    data = resp.json()
    assert_field(data, 'tokens', "Resposta tem 'tokens'")
    assert_field(data, 'tenant', "Resposta tem 'tenant'")
    assert_field(data, 'role',   "Resposta tem 'role'")

    tokens = data.get('tokens', {})
    assert_field(tokens, 'access',  "Tokens tem 'access'")
    assert_field(tokens, 'refresh', "Tokens tem 'refresh'")

    state['access_token']  = tokens.get('access')
    state['refresh_token'] = tokens.get('refresh')

    if data.get('role') == 'owner':
        ok("Role é 'owner'")
        state['passed'] += 1
    else:
        fail(f"Role deveria ser 'owner', recebeu '{data.get('role')}'")
        state['failed'] += 1

    tenant = data.get('tenant', {})
    if tenant.get('plan') == 'trial':
        ok("Tenant em plano trial")
        state['passed'] += 1

    # Verifica claims do JWT
    info(f"Token gerado: {state['access_token'][:40]}...")
    return True


def test_login_wrong_password():
    title("Validação — Senha errada")

    resp = requests.post(f"{BASE_URL}/auth/login/", json={
        "email":    state['email'],
        "password": "senhaErrada123",
    })

    assert_status(resp, 400, "POST /auth/login/ (senha errada)")


def test_me():
    title("ETAPA 1 — Me (sessão autenticada)")

    if not state['access_token']:
        warn("Pulando — sem token de acesso")
        return

    resp = requests.get(f"{BASE_URL}/auth/me/", headers=headers_auth())

    if not assert_status(resp, 200, "GET /auth/me/"):
        return

    data = resp.json()
    assert_field(data, 'user',          "Resposta tem 'user'")
    assert_field(data, 'tenant',        "Resposta tem 'tenant'")
    assert_field(data, 'role',          "Resposta tem 'role'")
    assert_field(data, 'can_access',    "Resposta tem 'can_access'")
    assert_field(data, 'trial_expired', "Resposta tem 'trial_expired'")

    if data.get('can_access') is True:
        ok("can_access = True (trial ativo)")
        state['passed'] += 1

    if data.get('trial_expired') is False:
        ok("trial_expired = False (trial válido)")
        state['passed'] += 1


def test_me_without_token():
    title("Validação — Me sem token")

    resp = requests.get(f"{BASE_URL}/auth/me/")
    assert_status(resp, 401, "GET /auth/me/ (sem token)")


def test_token_refresh():
    title("ETAPA 1 — Refresh de token")

    if not state['refresh_token']:
        warn("Pulando — sem refresh token")
        return

    resp = requests.post(f"{BASE_URL}/token/refresh/", json={
        "refresh": state['refresh_token'],
    })

    if not assert_status(resp, 200, "POST /token/refresh/"):
        return

    data = resp.json()
    assert_field(data, 'access', "Novo access token gerado")

    # Atualiza token para próximos testes
    state['access_token'] = data.get('access')
    ok("Token atualizado para próximos testes")
    state['passed'] += 1


def test_resend_verification():
    title("ETAPA 1 — Reenvio de verificação")

    resp = requests.post(f"{BASE_URL}/auth/resend-verification/", json={
        "email": state['email'],
    })

    assert_status(resp, 200, "POST /auth/resend-verification/")

    data = resp.json()
    if 'message' in data:
        ok(f"Mensagem: {data['message'][:60]}...")
        state['passed'] += 1


# ════════════════════════════════════════════════════════════════
# ETAPA 2 — TRIAL
# ════════════════════════════════════════════════════════════════

def test_trial_status():
    title("ETAPA 2 — Status do trial")

    if not state['access_token']:
        warn("Pulando — sem token de acesso")
        return

    resp = requests.get(f"{BASE_URL}/trial/status/", headers=headers_auth())

    if not assert_status(resp, 200, "GET /trial/status/"):
        return

    data = resp.json()
    assert_field(data, 'plan',                 "Tem 'plan'")
    assert_field(data, 'is_trial',             "Tem 'is_trial'")
    assert_field(data, 'is_trial_active',      "Tem 'is_trial_active'")
    assert_field(data, 'trial_days_remaining', "Tem 'trial_days_remaining'")
    assert_field(data, 'can_access',           "Tem 'can_access'")
    assert_field(data, 'max_professionals',    "Tem 'max_professionals'")

    if data.get('is_trial') is True:
        ok("is_trial = True")
        state['passed'] += 1

    if data.get('is_trial_active') is True:
        ok("is_trial_active = True")
        state['passed'] += 1

    if data.get('max_professionals') == 999:
        ok("Trial com acesso total (999 profissionais)")
        state['passed'] += 1

    info(f"Dias restantes: {data.get('trial_days_remaining')}")
    info(f"Expira em: {data.get('trial_ends_at', 'N/A')}")


def test_plans():
    title("ETAPA 2 — Listagem de planos")

    if not state['access_token']:
        warn("Pulando — sem token de acesso")
        return

    resp = requests.get(f"{BASE_URL}/plans/", headers=headers_auth())

    if not assert_status(resp, 200, "GET /plans/"):
        return

    data = resp.json()
    assert_field(data, 'plans', "Resposta tem 'plans'")

    plans = data.get('plans', [])

    if len(plans) == 4:
        ok(f"{len(plans)} planos retornados")
        state['passed'] += 1
    else:
        fail(f"Esperado 4 planos, recebeu {len(plans)}")
        state['failed'] += 1

    plan_ids = [p['id'] for p in plans]
    for expected_id in ['starter', 'pro', 'advanced', 'enterprise']:
        if expected_id in plan_ids:
            ok(f"Plano '{expected_id}' presente")
            state['passed'] += 1
        else:
            fail(f"Plano '{expected_id}' ausente")
            state['failed'] += 1

    # Verifica plano recomendado
    recommended = [p for p in plans if p.get('recommended')]
    if recommended:
        ok(f"Plano recomendado: {recommended[0]['id']}")
        state['passed'] += 1

    # Verifica preços com desconto anual
    for plan in plans:
        if plan.get('price_annual') and plan.get('price_monthly'):
            desconto = round((1 - plan['price_annual'] / (plan['price_monthly'] * 12)) * 100)
            info(f"Plano {plan['id']}: R${plan['price_monthly']}/mês | R${plan['price_annual']}/ano ({desconto}% off)")


# ════════════════════════════════════════════════════════════════
# RESUMO FINAL
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
    print(f"{BOLD}  Beauti API — Testes Etapa 1 e 2{RESET}")
    print(f"{BOLD}  Base URL: {BASE_URL}{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")

    # Etapa 1 — Auth
    test_register()
    test_register_duplicate_email()
    test_register_invalid_password()
    test_login()
    test_login_wrong_password()
    test_me()
    test_me_without_token()
    test_token_refresh()
    test_resend_verification()

    # Etapa 2 — Trial
    test_trial_status()
    test_plans()

    success = print_summary()
    sys.exit(0 if success else 1)