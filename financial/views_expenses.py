# financial/views_expenses.py
# Endpoints de Despesas e Contas a Pagar

from datetime import date, timedelta
from calendar import monthrange
from django.utils import timezone
from django.db.models import Sum
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from tenants.permissions import TenantAccessPermission
from financial.models import Expense, AccountsPayable, CashEntry


EXPENSE_CATEGORIES = [
    {'value': 'rent',        'label': 'Aluguel',           'emoji': '🏠'},
    {'value': 'energy',      'label': 'Energia elétrica',  'emoji': '⚡'},
    {'value': 'water',       'label': 'Água',              'emoji': '💧'},
    {'value': 'internet',    'label': 'Internet',          'emoji': '📶'},
    {'value': 'product',     'label': 'Compra de produto', 'emoji': '📦'},
    {'value': 'salary',      'label': 'Salário fixo',      'emoji': '👤'},
    {'value': 'commission',  'label': 'Comissão',          'emoji': '💰'},
    {'value': 'maintenance', 'label': 'Manutenção',        'emoji': '🔧'},
    {'value': 'marketing',   'label': 'Marketing',         'emoji': '📣'},
    {'value': 'other',       'label': 'Outros',            'emoji': '📋'},
]


def _to_date(value) -> date:
    """Converte string ou date para objeto date."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _serialize_expense(e: Expense) -> dict:
    d = _to_date(e.date)
    return {
        'id':          str(e.id),
        'category':    e.category,
        'description': e.description,
        'amount':      float(e.amount),
        'date':        d.isoformat(),
        'notes':       e.notes,
        'created_at':  e.created_at.isoformat(),
    }


def _serialize_payable(p: AccountsPayable) -> dict:
    due      = _to_date(p.due_date)
    today    = date.today()
    is_overdue = p.status == 'pending' and due < today
    return {
        'id':          str(p.id),
        'description': p.description,
        'category':    p.category,
        'amount':      float(p.amount),
        'due_date':    due.isoformat(),
        'recurrence':  p.recurrence,
        'status':      'overdue' if is_overdue else p.status,
        'notes':       p.notes,
        'paid_at':     p.paid_at.isoformat() if p.paid_at else None,
        'paid_amount': float(p.paid_amount) if p.paid_amount else None,
        'days_until':  (due - today).days,
    }


# ── DESPESAS ──────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def expenses_view(request):
    """
    GET  /api/financial/expenses/?date=2026-06-01  (ou year+month)
    POST /api/financial/expenses/  → lança despesa
    """
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method == 'GET':
        filter_date  = request.query_params.get('date')
        filter_month = request.query_params.get('month')
        filter_year  = request.query_params.get('year')
        category     = request.query_params.get('category')

        qs = Expense.objects.filter(tenant=tenant)

        if filter_date:
            qs = qs.filter(date=filter_date)
        elif filter_month and filter_year:
            _, last_day = monthrange(int(filter_year), int(filter_month))
            qs = qs.filter(
                date__gte=date(int(filter_year), int(filter_month), 1),
                date__lte=date(int(filter_year), int(filter_month), last_day),
            )
        if category:
            qs = qs.filter(category=category)

        total = sum(float(e.amount) for e in qs)

        return Response({
            'expenses':   [_serialize_expense(e) for e in qs],
            'total':      round(total, 2),
            'categories': EXPENSE_CATEGORIES,
        })

    # POST
    description = request.data.get('description', '').strip()
    amount      = request.data.get('amount')
    category    = request.data.get('category', 'other')
    exp_date    = request.data.get('date', date.today().isoformat())
    notes       = request.data.get('notes', '')

    if not description or not amount:
        return Response({'error': 'description e amount são obrigatórios.'}, status=400)

    expense = Expense.objects.create(
        tenant      = tenant,
        description = description,
        amount      = float(amount),
        category    = category,
        date        = _to_date(exp_date),
        notes       = notes,
        created_by  = request.user,
    )

    return Response({
        'message': 'Despesa lançada.',
        'expense': _serialize_expense(expense),
    }, status=201)


@api_view(['DELETE'])
@permission_classes([TenantAccessPermission])
def expense_detail_view(request, expense_id):
    """DELETE /api/financial/expenses/{id}/"""
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    try:
        expense = Expense.objects.get(id=expense_id, tenant=tenant)
    except Expense.DoesNotExist:
        return Response({'error': 'Despesa não encontrada.'}, status=404)

    expense.delete()
    return Response({'message': 'Despesa removida.'})


# ── CONTAS A PAGAR ────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def payables_view(request):
    """
    GET  /api/financial/payables/?status=pending
    POST /api/financial/payables/  → cria conta a pagar
    """
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method == 'GET':
        status_filter = request.query_params.get('status', 'all')
        qs = AccountsPayable.objects.filter(tenant=tenant)

        if status_filter == 'pending':
            qs = qs.filter(status='pending')
        elif status_filter == 'paid':
            qs = qs.filter(status='paid')

        today   = date.today()
        all_ps  = list(qs)

        overdue  = [p for p in all_ps if p.status == 'pending' and _to_date(p.due_date) < today]
        pending  = [p for p in all_ps if p.status == 'pending' and _to_date(p.due_date) >= today]
        paid     = [p for p in all_ps if p.status == 'paid']
        upcoming = [p for p in pending if 0 <= (_to_date(p.due_date) - today).days <= 30]

        return Response({
            'payables': [_serialize_payable(p) for p in all_ps],
            'summary': {
                'total_pending':  round(sum(float(p.amount) for p in pending), 2),
                'total_overdue':  round(sum(float(p.amount) for p in overdue), 2),
                'total_paid':     round(sum(float(p.paid_amount or p.amount) for p in paid), 2),
                'upcoming_30d':   round(sum(float(p.amount) for p in upcoming), 2),
                'count_overdue':  len(overdue),
                'count_pending':  len(pending),
            },
            'categories': EXPENSE_CATEGORIES,
        })

    # POST
    description = request.data.get('description', '').strip()
    amount      = request.data.get('amount')
    due_date    = request.data.get('due_date')
    category    = request.data.get('category', 'other')
    recurrence  = request.data.get('recurrence', 'once')
    notes       = request.data.get('notes', '')

    if not description or not amount or not due_date:
        return Response({'error': 'description, amount e due_date são obrigatórios.'}, status=400)

    base_date = _to_date(due_date)

    payable = AccountsPayable.objects.create(
        tenant      = tenant,
        description = description,
        amount      = float(amount),
        due_date    = base_date,
        category    = category,
        recurrence  = recurrence,
        notes       = notes,
        created_by  = request.user,
    )

    # Mensal → cria os próximos 11 meses sempre no mesmo dia
    if recurrence == 'monthly':
        from dateutil.relativedelta import relativedelta
        for i in range(1, 12):
            AccountsPayable.objects.create(
                tenant      = tenant,
                description = description,
                amount      = float(amount),
                due_date    = base_date + relativedelta(months=i),
                category    = category,
                recurrence  = recurrence,
                notes       = notes,
                created_by  = request.user,
            )

    return Response({
        'message': 'Conta a pagar criada.' + (' (12 parcelas geradas)' if recurrence == 'monthly' else ''),
        'payable': _serialize_payable(payable),
    }, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def payable_detail_view(request, payable_id):
    """
    PATCH  /api/financial/payables/{id}/  → marcar como pago / editar
    DELETE /api/financial/payables/{id}/  → remover
    """
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    try:
        payable = AccountsPayable.objects.get(id=payable_id, tenant=tenant)
    except AccountsPayable.DoesNotExist:
        return Response({'error': 'Conta não encontrada.'}, status=404)

    if request.method == 'PATCH':
        if request.data.get('action') == 'pay':
            paid_amount = request.data.get('paid_amount', payable.amount)
            payable.status      = AccountsPayable.Status.PAID
            payable.paid_at     = timezone.now()
            payable.paid_amount = float(paid_amount)
            payable.save()

            # Lança automaticamente como despesa
            Expense.objects.create(
                tenant      = tenant,
                description = payable.description,
                amount      = float(paid_amount),
                category    = payable.category,
                date        = date.today(),
                notes       = 'Pago via contas a pagar',
                created_by  = request.user,
            )

            return Response({
                'message': f'{payable.description} marcado como pago.',
                'payable': _serialize_payable(payable),
            })

        # Editar campos
        for field in ['description', 'amount', 'category', 'notes']:
            if field in request.data:
                setattr(payable, field, request.data[field])
        if 'due_date' in request.data:
            payable.due_date = _to_date(request.data['due_date'])
        payable.save()
        return Response({'message': 'Atualizado.', 'payable': _serialize_payable(payable)})

    if request.method == 'DELETE':
        payable.delete()
        return Response({'message': 'Conta removida.'})


# ── VISÃO FINANCEIRA COMPLETA ─────────────────────────────────

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def financial_overview_view(request):
    """
    GET /api/financial/overview/?year=2026&month=6
    Visão completa: receita, despesas, lucro, produtos vendidos, contas a pagar
    """
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    today = date.today()
    year  = int(request.query_params.get('year',  today.year))
    month = int(request.query_params.get('month', today.month))

    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end   = date(year, month, last_day)

    # Receita
    entries    = CashEntry.objects.filter(tenant=tenant, created_at__date__gte=month_start, created_at__date__lte=month_end)
    revenue    = sum(float(e.amount) for e in entries)
    commission = sum(float(e.commission_amount) for e in entries)

    # Despesas
    expenses = Expense.objects.filter(
        tenant=tenant,
        date__gte=month_start,
        date__lte=month_end,
    ).exclude(category='commission')  # ← ADICIONAR

    total_expenses = sum(float(e.amount) for e in expenses)

    # Despesas por categoria
    exp_by_cat: dict = {}
    for e in expenses:
        cat = e.get_category_display()
        exp_by_cat[cat] = exp_by_cat.get(cat, 0) + float(e.amount)

    # Produtos vendidos
    from financial.models import CommandaItem, Comanda
    sold_items = CommandaItem.objects.filter(
        comanda__tenant=tenant,
        comanda__status=Comanda.Status.CLOSED,
        comanda__closed_at__date__gte=month_start,
        comanda__closed_at__date__lte=month_end,
        product__isnull=False,
    ).select_related('product')

    products_sold: dict = {}
    products_revenue = 0.0
    products_cost    = 0.0
    for item in sold_items:
        name = item.product.name
        if name not in products_sold:
            products_sold[name] = {'quantity': 0, 'revenue': 0.0, 'cost': 0.0, 'profit': 0.0}
        qty  = item.quantity
        rev  = float(item.total)
        cost = float(item.product.cost_price) * qty
        products_sold[name]['quantity'] += qty
        products_sold[name]['revenue']  += rev
        products_sold[name]['cost']     += cost
        products_sold[name]['profit']   += rev - cost
        products_revenue += rev
        products_cost    += cost

    # Lucro
    gross_profit = revenue - commission
    net_profit   = gross_profit - total_expenses

    # Contas a pagar do mês
    payables          = AccountsPayable.objects.filter(tenant=tenant, due_date__gte=month_start, due_date__lte=month_end)
    pending_payables  = [p for p in payables if p.status == 'pending']
    paid_payables     = [p for p in payables if p.status == 'paid']

    return Response({
        'period': f"{month_start.isoformat()} a {month_end.isoformat()}",
        'summary': {
            'revenue':          round(revenue, 2),
            'commission':       round(commission, 2),
            'gross_profit':     round(gross_profit, 2),
            'expenses':         round(total_expenses, 2),
            'net_profit':       round(net_profit, 2),
            'margin_pct':       round((net_profit / revenue * 100), 1) if revenue else 0,
            'products_revenue': round(products_revenue, 2),
            'products_cost':    round(products_cost, 2),
            'products_profit':  round(products_revenue - products_cost, 2),
        },
        'expenses_list': [{
            'id':          str(e.id),
            'category':    e.get_category_display(),
            'description': e.description,
            'amount':      float(e.amount),
            'date':        _to_date(e.date).isoformat(),
        } for e in expenses],
        'expenses_by_category': [
            {'category': cat, 'amount': round(amt, 2)}
            for cat, amt in sorted(exp_by_cat.items(), key=lambda x: -x[1])
        ],
        'products_sold': [
            {'name': name, **data}
            for name, data in sorted(products_sold.items(), key=lambda x: -x[1]['revenue'])
        ],
        'payables_summary': {
            'pending': round(sum(float(p.amount) for p in pending_payables), 2),
            'paid':    round(sum(float(p.paid_amount or p.amount) for p in paid_payables), 2),
            'overdue': round(sum(float(p.amount) for p in pending_payables if _to_date(p.due_date) < today), 2),
        },
        'payables': [_serialize_payable(p) for p in payables],
    })