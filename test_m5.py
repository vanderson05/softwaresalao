"""
test_m5.py — Testes do M5: Produtos, Estoque, Comanda, Caixa e Relatórios

Uso:
    python test_m5.py
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
    'email':           f"m5_{datetime.now().strftime('%H%M%S')}@beauti.com",
    'password':        'Senha@123',
    'owner_token':     None,
    'professional_id': None,
    'service_id':      None,
    'appointment_id':  None,
    'appointment_id2': None,
    'product_id':      None,
    'comanda_item_id': None,
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
        info(f"Resposta: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:400]}")
    except Exception:
        info(f"Resposta: {resp.text[:200]}")
    state['failed'] += 1
    state['errors'].append(test_name)
    return False

def h():
    return {'Authorization': f"Bearer {state['owner_token']}", 'Content-Type': 'application/json'}

def next_weekday():
    today = date.today()
    for i in range(1, 8):
        d = today + timedelta(days=i)
        if d.weekday() < 5:
            return d
    return today + timedelta(days=1)


# ════════════════════════════════════════════════════════════════
# SETUP
# ════════════════════════════════════════════════════════════════

def setup():
    title("SETUP — Criando tenant com agendamentos para testar M5")

    resp = requests.post(f"{API_URL}/auth/register/", json={
        "business_name": "Barbearia M5 Test",
        "phone": "19999999999",
        "email": state['email'],
        "password": state['password'],
        "type": "barbershop",
    })
    if resp.status_code != 201:
        fail("Registro falhou"); return False

    resp = requests.post(f"{API_URL}/auth/login/", json={"email": state['email'], "password": state['password']})
    state['owner_token'] = resp.json()['tokens']['access']
    ok("Login OK")

    # Setup completo
    requests.patch(f"{API_URL}/setup/establishment/", headers=h(), json={
        "address": "Rua Teste, 1", "city": "Americana",
        "business_hours": [{"weekday": i, "open_time": "09:00", "close_time": "18:00"} for i in range(6)]
            + [{"weekday": 6, "is_closed": True}]
    })

    resp = requests.post(f"{API_URL}/professionals/", headers=h(), json={"name": "Carlão", "commission_pct": 40, "slot_interval": 30})
    state['professional_id'] = resp.json()['id']

    resp = requests.post(f"{API_URL}/services/", headers=h(), json={"name": "Corte masculino", "duration_min": 30, "price": 35.00})
    state['service_id'] = resp.json()['id']

    requests.post(f"{API_URL}/schedules/bulk/", headers=h(), json={
        "professional_id": state['professional_id'],
        "schedules": [{"weekday": i, "start_time": "09:00", "end_time": "18:00"} for i in range(5)]
    })
    requests.post(f"{API_URL}/setup/complete/", headers=h())

    # Cria 2 agendamentos
    d = next_weekday()
    resp = requests.post(f"{API_URL}/appointments/", headers=h(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{d.isoformat()}T09:00:00",
        "client_name":     "João Silva",
        "client_phone":    f"199{datetime.now().strftime('%H%M%S')}",
        "source":          "panel",
    })
    state['appointment_id'] = resp.json()['id']

    resp = requests.post(f"{API_URL}/appointments/", headers=h(), json={
        "professional_id": state['professional_id'],
        "service_id":      state['service_id'],
        "starts_at":       f"{d.isoformat()}T10:00:00",
        "client_name":     "Maria Santos",
        "client_phone":    f"198{datetime.now().strftime('%H%M%S')}",
        "source":          "panel",
    })
    state['appointment_id2'] = resp.json()['id']

    ok(f"Setup completo — 2 agendamentos criados para {d.isoformat()}")
    return True


# ════════════════════════════════════════════════════════════════
# PRODUTOS
# ════════════════════════════════════════════════════════════════

def test_products():
    title("M5 — Produtos")

    # Criar produto com estoque
    resp = requests.post(f"{API_URL}/financial/products/", headers=h(), json={
        "name":        "Pomada Capilar",
        "category":    "product",
        "price":       25.00,
        "cost_price":  12.00,
        "stock_qty":   20,
        "stock_alert": 5,
        "track_stock": True,
    })
    if assert_status(resp, 201, "POST /financial/products/ (Pomada)"):
        data = resp.json()
        state['product_id'] = data['id']
        info(f"Produto criado: {data['name']} — R${data['price']}")

    # Produto sem estoque (gorjeta)
    resp = requests.post(f"{API_URL}/financial/products/", headers=h(), json={
        "name":        "Gorjeta",
        "category":    "other",
        "price":       0,
        "track_stock": False,
    })
    assert_status(resp, 201, "POST /financial/products/ (Gorjeta sem estoque)")

    # Listar
    resp = requests.get(f"{API_URL}/financial/products/", headers=h())
    if assert_status(resp, 200, "GET /financial/products/"):
        data = resp.json()
        assert_ok(len(data) >= 1, f"{len(data)} produto(s)")
        assert_ok('stock_qty' in data[0], "Tem 'stock_qty'")
        assert_ok('margin_pct' in data[0], "Tem 'margin_pct'")

    # Detalhe com movimentações
    if state['product_id']:
        resp = requests.get(f"{API_URL}/financial/products/{state['product_id']}/", headers=h())
        if assert_status(resp, 200, "GET /financial/products/{id}/"):
            data = resp.json()
            assert_ok('movements' in data, "Tem 'movements'")
            assert_ok(data['margin_pct'] > 0, f"Margem calculada: {data['margin_pct']}%")

    # Editar
    if state['product_id']:
        resp = requests.patch(f"{API_URL}/financial/products/{state['product_id']}/", headers=h(), json={"price": 28.00})
        assert_status(resp, 200, "PATCH /financial/products/{id}/")


def test_stock():
    title("M5 — Estoque")

    if not state['product_id']:
        warn("Pulando — sem product_id")
        return

    # Entrada de estoque
    resp = requests.post(f"{API_URL}/financial/products/{state['product_id']}/stock/", headers=h(), json={
        "type":       "in",
        "quantity":   10,
        "reason":     "Compra fornecedor",
        "cost_price": 11.00,
    })
    if assert_status(resp, 201, "POST /financial/products/{id}/stock/ (entrada)"):
        data = resp.json()
        assert_ok('stock_qty' in data, "Tem 'stock_qty'")
        info(f"Estoque após entrada: {data['stock_qty']} unidades")

    # Alerta de estoque baixo — cria produto com estoque baixo
    resp = requests.post(f"{API_URL}/financial/products/", headers=h(), json={
        "name":        "Produto Baixo",
        "price":       10.00,
        "stock_qty":   2,
        "stock_alert": 5,
        "track_stock": True,
    })

    resp = requests.get(f"{API_URL}/financial/stock/alerts/", headers=h())
    if assert_status(resp, 200, "GET /financial/stock/alerts/"):
        data = resp.json()
        assert_ok('alerts' in data, "Tem 'alerts'")
        assert_ok(data['total'] >= 1, f"{data['total']} alerta(s) de estoque baixo")
        info(f"Produto com estoque baixo: {data['alerts'][0]['name'] if data['alerts'] else 'nenhum'}")


# ════════════════════════════════════════════════════════════════
# COMANDA
# ════════════════════════════════════════════════════════════════

def test_comanda_open():
    title("M5 — Abrir comanda")

    if not state['appointment_id']:
        warn("Pulando"); return

    resp = requests.get(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h()
    )
    if not assert_status(resp, 200, "GET /financial/appointments/{id}/comanda/ (abre)"):
        return

    data = resp.json()
    assert_ok('id' in data,       "Comanda tem 'id'")
    assert_ok('items' in data,    "Comanda tem 'items'")
    assert_ok('total' in data,    "Comanda tem 'total'")
    assert_ok('status' in data,   "Comanda tem 'status'")
    assert_ok(data['status'] == 'open', "Status = open")
    assert_ok(len(data['items']) == 1,  "1 item automático (serviço do agendamento)")

    item = data['items'][0]
    assert_ok(item['description'] == 'Corte masculino', "Serviço adicionado automaticamente")
    assert_ok(item['unit_price'] == 35.0,               "Preço do serviço correto")
    assert_ok(item['commission_pct'] == 40.0,           "Comissão do profissional copiada")

    info(f"Comanda aberta — Total: R${data['total']} | Comissão: R${data['total_commission']}")

    # Reabre a mesma comanda — deve retornar a existente
    resp2 = requests.get(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h()
    )
    if assert_status(resp2, 200, "GET comanda novamente (idempotente)"):
        assert_ok(resp2.json()['id'] == data['id'], "Mesma comanda retornada")


def test_comanda_add_items():
    title("M5 — Adicionar itens na comanda")

    if not state['appointment_id']:
        warn("Pulando"); return

    # Adiciona produto com estoque
    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h(),
        json={
            "product_id": state['product_id'],
            "quantity":   1,
            "discount":   0,
        }
    )
    if assert_status(resp, 201, "POST comanda (adiciona Pomada Capilar)"):
        data = resp.json()
        assert_ok('item' in data,          "Tem 'item'")
        assert_ok('comanda_total' in data,  "Tem 'comanda_total'")
        state['comanda_item_id'] = data['item']['id']
        info(f"Total após pomada: R${data['comanda_total']}")

    # Verifica estoque descontado
    if state['product_id']:
        resp = requests.get(f"{API_URL}/financial/products/{state['product_id']}/", headers=h())
        if resp.status_code == 200:
            stock = resp.json()['stock_qty']
            info(f"Estoque após venda: {stock} unidades")

    # Adiciona gorjeta (sem produto, sem estoque)
    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h(),
        json={
            "description": "Gorjeta",
            "quantity":    1,
            "unit_price":  10.00,
            "is_courtesy": False,
            "commission_pct": 0,
        }
    )
    assert_status(resp, 201, "POST comanda (adiciona Gorjeta)")

    # Adiciona cortesia (não gera comissão)
    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h(),
        json={
            "description":  "Shampoo cortesia",
            "quantity":     1,
            "unit_price":   15.00,
            "is_courtesy":  True,
            "commission_pct": 40,
        }
    )
    if assert_status(resp, 201, "POST comanda (cortesia)"):
        item = resp.json()['item']
        assert_ok(item['commission_value'] == 0, "Cortesia não gera comissão")

    # Verifica comanda com todos os itens
    resp = requests.get(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h()
    )
    if resp.status_code == 200:
        data = resp.json()
        assert_ok(len(data['items']) == 4, f"4 itens na comanda ({len(data['items'])} encontrados)")
        info(f"Total final: R${data['total']} | Comissão: R${data['total_commission']}")


def test_comanda_edit_item():
    title("M5 — Editar item da comanda")

    if not state['comanda_item_id']:
        warn("Pulando"); return

    # Aplica desconto no item
    resp = requests.patch(
        f"{API_URL}/financial/comanda/items/{state['comanda_item_id']}/",
        headers=h(),
        json={"discount": 5.00}
    )
    if assert_status(resp, 200, "PATCH /financial/comanda/items/{id}/ (desconto)"):
        item = resp.json()['item']
        assert_ok(item['discount'] == 5.0, "Desconto de R$5 aplicado")
        info(f"Após desconto: R${item['total']}")


def test_comanda_checkout():
    title("M5 — Checkout (fecha comanda + completa agendamento)")

    if not state['appointment_id']:
        warn("Pulando"); return

    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/checkout/",
        headers=h(),
        json={"payment_method": "pix"}
    )
    if not assert_status(resp, 200, "POST /financial/appointments/{id}/checkout/"):
        return

    data = resp.json()
    assert_ok('total' in data,           "Tem 'total'")
    assert_ok('commission' in data,      "Tem 'commission'")
    assert_ok('payment_method' in data,  "Tem 'payment_method'")
    assert_ok('comanda' in data,         "Tem 'comanda'")
    assert_ok(data['status'] == 'completed', "Agendamento marcado como completed")
    assert_ok(data['comanda']['status'] == 'closed', "Comanda fechada")
    assert_ok(data['payment_method'] == 'pix', "Pagamento = pix")

    info(f"Total: R${data['total']} | Comissão Carlão (40%): R${data['commission']}")

    # Tenta fazer checkout novamente
    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/checkout/",
        headers=h(),
        json={"payment_method": "pix"}
    )
    assert_status(resp, 400, "POST checkout novamente → 400")

    # Tenta adicionar item em comanda fechada
    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id']}/comanda/",
        headers=h(),
        json={"description": "Item pós fechamento", "unit_price": 10}
    )
    assert_status(resp, 400, "POST item em comanda fechada → 400")


def test_checkout_sem_comanda():
    title("M5 — Checkout direto (sem abrir comanda antes)")

    if not state['appointment_id2']:
        warn("Pulando"); return

    # Checkout direto — cria comanda + adiciona serviço + fecha tudo
    resp = requests.post(
        f"{API_URL}/financial/appointments/{state['appointment_id2']}/checkout/",
        headers=h(),
        json={"payment_method": "cash"}
    )
    if assert_status(resp, 200, "POST checkout direto (sem abrir comanda antes)"):
        data = resp.json()
        assert_ok(data['status'] == 'completed',       "Agendamento completed")
        assert_ok(data['total'] == 35.0,               "Total = R$35 (só o serviço)")
        assert_ok(data['payment_method'] == 'cash',    "Pagamento = cash")
        assert_ok(data['comanda']['status'] == 'closed', "Comanda fechada automaticamente")
        info(f"Checkout direto: R${data['total']} em dinheiro")


# ════════════════════════════════════════════════════════════════
# CAIXA E RELATÓRIOS
# ════════════════════════════════════════════════════════════════

def test_cashbox():
    title("M5 — Caixa do dia")

    today = date.today()
    d     = next_weekday()

    # Caixa do dia dos agendamentos criados
    resp = requests.get(f"{API_URL}/financial/cashbox/", headers=h(), params={'date': d.isoformat()})
    if assert_status(resp, 200, f"GET /financial/cashbox/?date={d.isoformat()}"):
        data = resp.json()
        assert_ok('total_revenue' in data,    "Tem 'total_revenue'")
        assert_ok('by_payment' in data,       "Tem 'by_payment'")
        assert_ok('by_professional' in data,  "Tem 'by_professional'")
        assert_ok('appointments' in data,     "Tem 'appointments'")
        assert_ok('avg_ticket' in data,       "Tem 'avg_ticket'")
        info(f"Receita do dia: R${data['total_revenue']}")
        info(f"Atendimentos: {data['appointments']['completed']} realizados")

    # Caixa de hoje (padrão)
    resp = requests.get(f"{API_URL}/financial/cashbox/", headers=h())
    assert_status(resp, 200, "GET /financial/cashbox/ (hoje, padrão)")


def test_report_monthly():
    title("M5 — Relatório mensal")

    today = date.today()
    resp  = requests.get(
        f"{API_URL}/financial/report/monthly/",
        headers=h(),
        params={'year': today.year, 'month': today.month}
    )
    if assert_status(resp, 200, "GET /financial/report/monthly/"):
        data = resp.json()
        assert_ok('summary' in data,         "Tem 'summary'")
        assert_ok('by_professional' in data, "Tem 'by_professional'")
        assert_ok('by_service' in data,      "Tem 'by_service'")
        assert_ok('by_payment' in data,      "Tem 'by_payment'")
        assert_ok('by_week' in data,         "Tem 'by_week'")

        summary = data['summary']
        assert_ok('total_revenue' in summary,    "Summary tem 'total_revenue'")
        assert_ok('avg_ticket' in summary,       "Summary tem 'avg_ticket'")
        assert_ok('total_appointments' in summary, "Summary tem 'total_appointments'")
        info(f"Receita do mês: R${summary['total_revenue']}")


def test_commissions():
    title("M5 — Comissões do mês")

    today = date.today()
    resp  = requests.get(
        f"{API_URL}/financial/commissions/",
        headers=h(),
        params={'year': today.year, 'month': today.month}
    )
    if assert_status(resp, 200, "GET /financial/commissions/"):
        data = resp.json()
        assert_ok('total_to_pay' in data,   "Tem 'total_to_pay'")
        assert_ok('professionals' in data,  "Tem 'professionals'")
        assert_ok('period' in data,         "Tem 'period'")

        if data['professionals']:
            prof = data['professionals'][0]
            assert_ok('commission_pct' in prof,    "Profissional tem 'commission_pct'")
            assert_ok('revenue_generated' in prof, "Profissional tem 'revenue_generated'")
            assert_ok('commission_total' in prof,  "Profissional tem 'commission_total'")
            info(f"Carlão: gerou R${prof['revenue_generated']} → comissão R${prof['commission_total']}")
        info(f"Total a pagar em comissões: R${data['total_to_pay']}")


# ════════════════════════════════════════════════════════════════
# RESUMO
# ════════════════════════════════════════════════════════════════

def print_summary():
    title("RESUMO DOS TESTES M5")
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
    print(f"\n{BOLD}{'═'*50}{RESET}")
    print(f"{BOLD}  Beauti — Testes M5: Financeiro + Comanda + Estoque{RESET}")
    print(f"{BOLD}{'═'*50}{RESET}")

    if not setup():
        sys.exit(1)

    test_products()
    test_stock()
    test_comanda_open()
    test_comanda_add_items()
    test_comanda_edit_item()
    test_comanda_checkout()
    test_checkout_sem_comanda()
    test_cashbox()
    test_report_monthly()
    test_commissions()

    success = print_summary()
    sys.exit(0 if success else 1)