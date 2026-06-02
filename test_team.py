"""
test_team.py — Testes de gestão de equipe

Uso: python test_team.py
"""

import requests, json, sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
API_URL  = f"{BASE_URL}/api"
GREEN = "\033[92m"; RED = "\033[91m"; BLUE = "\033[94m"; RESET = "\033[0m"; BOLD = "\033[1m"

def ok(m):    print(f"  {GREEN}✓ {m}{RESET}")
def fail(m):  print(f"  {RED}✗ {m}{RESET}")
def info(m):  print(f"  {BLUE}→ {m}{RESET}")
def title(m): print(f"\n{BOLD}{BLUE}{'─'*50}{RESET}\n{BOLD}{m}{RESET}")

ts = datetime.now().strftime('%H%M%S')
state = {
    'email':    f"team_{ts}@beauti.com",
    'password': 'Senha@123',
    'owner_token': None,
    'professional_id': None,
    'manager_id':   None,
    'recept_id':    None,
    'prof_member_id': None,
    'manager_token':  None,
    'recept_token':   None,
    'prof_token':     None,
    'errors': [], 'passed': 0, 'failed': 0,
}

def assert_ok(c, t):
    if c: ok(t); state['passed'] += 1; return True
    fail(t); state['failed'] += 1; state['errors'].append(t); return False

def assert_status(r, e, t):
    if r.status_code == e: ok(f"{t} — {r.status_code}"); state['passed'] += 1; return True
    fail(f"{t} — esperado {e}, recebeu {r.status_code}")
    try: info(json.dumps(r.json(), indent=2, ensure_ascii=False)[:300])
    except: info(r.text[:200])
    state['failed'] += 1; state['errors'].append(t); return False

def h(token=None):
    token = token or state['owner_token']
    return {'Authorization': f"Bearer {token}", 'Content-Type': 'application/json'}


def setup():
    title("SETUP")
    resp = requests.post(f"{API_URL}/auth/register/", json={
        "business_name": "Barbearia Team Test", "phone": "19999999999",
        "email": state['email'], "password": state['password'], "type": "barbershop",
    })
    if resp.status_code != 201: fail("Registro"); return False

    resp = requests.post(f"{API_URL}/auth/login/", json={"email": state['email'], "password": state['password']})
    state['owner_token'] = resp.json()['tokens']['access']

    requests.patch(f"{API_URL}/setup/establishment/", headers=h(), json={
        "address": "Rua A, 1", "city": "Americana",
        "business_hours": [{"weekday": i, "open_time": "09:00", "close_time": "18:00"} for i in range(5)] +
                          [{"weekday": 5, "is_closed": True}, {"weekday": 6, "is_closed": True}]
    })
    resp = requests.post(f"{API_URL}/professionals/", headers=h(), json={
        "name": "Carlão", "commission_pct": 40, "slot_interval": 30
    })
    state['professional_id'] = resp.json()['id']
    resp = requests.post(f"{API_URL}/services/", headers=h(), json={"name": "Corte", "duration_min": 30, "price": 35})
    requests.post(f"{API_URL}/schedules/bulk/", headers=h(), json={
        "professional_id": state['professional_id'],
        "schedules": [{"weekday": i, "start_time": "09:00", "end_time": "18:00"} for i in range(5)]
    })
    requests.post(f"{API_URL}/setup/complete/", headers=h())
    ok(f"Tenant: {state['email'][:20]}... | Profissional: Carlão")
    return True


def test_create_members():
    title("Equipe — Criar membros")

    # Gerente (administrativo)
    resp = requests.post(f"{API_URL}/team/", headers=h(), json={
        "name": "João Gerente", "email": f"gerente_{ts}@beauti.com",
        "password": "Senha@123", "role": "manager", "title": "Gerente Geral",
    })
    if assert_status(resp, 201, "POST /team/ (manager)"):
        state['manager_id'] = resp.json()['member']['id']
        info(f"Gerente: {resp.json()['member']['name']} | cargo: {resp.json()['member']['title']}")

    # Recepcionista
    resp = requests.post(f"{API_URL}/team/", headers=h(), json={
        "name": "Maria Recep", "email": f"recep_{ts}@beauti.com",
        "password": "Senha@123", "role": "receptionist", "title": "Recepcionista",
    })
    if assert_status(resp, 201, "POST /team/ (receptionist)"):
        state['recept_id'] = resp.json()['member']['id']

    # Profissional vinculado ao Carlão
    resp = requests.post(f"{API_URL}/team/", headers=h(), json={
        "name": "Carlão Silva", "email": f"carlao_{ts}@beauti.com",
        "password": "Senha@123", "role": "professional", "title": "Barbeiro",
        "professional_id": state['professional_id'],
    })
    if assert_status(resp, 201, "POST /team/ (professional vinculado)"):
        state['prof_member_id'] = resp.json()['member']['id']
        m = resp.json()['member']
        assert_ok(m.get('professional') is not None, "Vinculado ao Professional")
        info(f"Profissional: {m['name']} → agenda de {m.get('professional', {}).get('name', '—')}")

    # Listar equipe
    resp = requests.get(f"{API_URL}/team/", headers=h())
    if assert_status(resp, 200, "GET /team/"):
        members = resp.json()
        assert_ok(len(members) >= 4, f"{len(members)} membros (owner + 3 novos)")
        for m in members:
            assert_ok('role' in m and 'title' in m, f"{m.get('name','?')} tem role e title")


def test_login_by_role():
    title("Equipe — Login por role")

    # Manager login
    resp = requests.post(f"{API_URL}/auth/login/", json={"email": f"gerente_{ts}@beauti.com", "password": "Senha@123"})
    if assert_status(resp, 200, "Login gerente"):
        state['manager_token'] = resp.json()['tokens']['access']
        assert_ok(resp.json().get('role') == 'manager', "role = manager")
        assert_ok(resp.json().get('title') == 'Gerente Geral', "title = Gerente Geral")

    # Receptionist login
    resp = requests.post(f"{API_URL}/auth/login/", json={"email": f"recep_{ts}@beauti.com", "password": "Senha@123"})
    if assert_status(resp, 200, "Login recepcionista"):
        state['recept_token'] = resp.json()['tokens']['access']
        assert_ok(resp.json().get('role') == 'receptionist', "role = receptionist")

    # Professional login
    resp = requests.post(f"{API_URL}/auth/login/", json={"email": f"carlao_{ts}@beauti.com", "password": "Senha@123"})
    if assert_status(resp, 200, "Login profissional"):
        state['prof_token'] = resp.json()['tokens']['access']
        assert_ok(resp.json().get('role') == 'professional', "role = professional")


def test_permissions():
    title("Equipe — Permissões por role")

    # Manager pode ver agenda
    if state['manager_token']:
        resp = requests.get(f"{API_URL}/agenda/day/", headers=h(state['manager_token']))
        assert_status(resp, 200, "Manager: GET /agenda/day/ ✓")

        # Manager NÃO pode criar equipe
        resp = requests.post(f"{API_URL}/team/", headers=h(state['manager_token']), json={
            "name": "X", "email": "x@x.com", "password": "123456", "role": "professional"
        })
        assert_ok(resp.status_code == 403, "Manager: POST /team/ → 403 ✓")

    # Receptionist pode ver agenda
    if state['recept_token']:
        resp = requests.get(f"{API_URL}/agenda/day/", headers=h(state['recept_token']))
        assert_status(resp, 200, "Receptionist: GET /agenda/day/ ✓")

        # Receptionist NÃO pode ver financeiro
        resp = requests.get(f"{API_URL}/financial/cashbox/", headers=h(state['recept_token']))
        assert_ok(resp.status_code in [403, 404], "Receptionist: GET /financial/cashbox/ → sem acesso ✓")

    # Professional pode ver agenda
    if state['prof_token']:
        resp = requests.get(f"{API_URL}/agenda/day/", headers=h(state['prof_token']))
        assert_status(resp, 200, "Professional: GET /agenda/day/ ✓")

        # Professional NÃO pode criar profissional
        resp = requests.post(f"{API_URL}/professionals/", headers=h(state['prof_token']), json={
            "name": "Hack", "commission_pct": 0, "slot_interval": 30
        })
        assert_ok(resp.status_code in [403, 400], "Professional: POST /professionals/ → sem acesso ✓")


def test_update_member():
    title("Equipe — Atualizar membro")

    if not state['manager_id']: return

    # Atualizar title e role
    resp = requests.patch(f"{API_URL}/team/{state['manager_id']}/", headers=h(), json={
        "title": "Gerente Sênior",
        "role":  "receptionist",
    })
    if assert_status(resp, 200, "PATCH /team/{id}/ (title + role)"):
        m = resp.json()['member']
        assert_ok(m['title'] == 'Gerente Sênior', "title atualizado")
        assert_ok(m['role']  == 'receptionist',   "role atualizado")

    # Atualizar senha
    resp = requests.patch(f"{API_URL}/team/{state['manager_id']}/", headers=h(), json={
        "new_password": "NovaSenha@456"
    })
    assert_status(resp, 200, "PATCH /team/{id}/ (nova senha)")

    # Login com nova senha
    resp = requests.post(f"{API_URL}/auth/login/", json={
        "email": f"gerente_{ts}@beauti.com", "password": "NovaSenha@456"
    })
    assert_status(resp, 200, "Login com nova senha")

    # Bloquear acesso
    resp = requests.patch(f"{API_URL}/team/{state['recept_id']}/", headers=h(), json={"is_active": False})
    if assert_status(resp, 200, "PATCH /team/{id}/ (bloquear)"):
        resp2 = requests.post(f"{API_URL}/auth/login/", json={
            "email": f"recep_{ts}@beauti.com", "password": "Senha@123"
        })
        assert_ok(resp2.status_code != 200, "Login bloqueado após desativar ✓")


def test_remove_member():
    title("Equipe — Remover membro")

    if not state['recept_id']: return

    resp = requests.delete(f"{API_URL}/team/{state['recept_id']}/", headers=h())
    assert_status(resp, 200, "DELETE /team/{id}/")

    # Não aparece mais na lista
    resp = requests.get(f"{API_URL}/team/", headers=h())
    if resp.status_code == 200:
        ids = [m['id'] for m in resp.json()]
        assert_ok(state['recept_id'] not in ids, "Membro removido da lista ✓")

    # Owner não pode ser removido
    resp = requests.get(f"{API_URL}/team/", headers=h())
    if resp.status_code == 200:
        owner = next((m for m in resp.json() if m['role'] == 'owner'), None)
        if owner:
            resp2 = requests.delete(f"{API_URL}/team/{owner['id']}/", headers=h())
            assert_ok(resp2.status_code in [400, 403], "Owner não pode ser removido ✓")


def print_summary():
    title("RESUMO — Gestão de Equipe")
    total = state['passed'] + state['failed']
    print(f"\n  Total:    {total}")
    print(f"  {GREEN}Passou:   {state['passed']}{RESET}")
    print(f"  {RED}Falhou:   {state['failed']}{RESET}")
    if state['errors']:
        print(f"\n  {RED}Falhas:{RESET}")
        for e in state['errors']: print(f"    {RED}• {e}{RESET}")
    else:
        print(f"\n  {GREEN}{BOLD}Todos os testes passaram! ✓{RESET}")
    print()
    return state['failed'] == 0


if __name__ == '__main__':
    print(f"\n{BOLD}{'═'*50}{RESET}")
    print(f"{BOLD}  Beauti — Gestão de Equipe{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")
    if not setup(): sys.exit(1)
    test_create_members()
    test_login_by_role()
    test_permissions()
    test_update_member()
    test_remove_member()
    sys.exit(0 if print_summary() else 1)