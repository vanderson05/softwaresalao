# financial/views.py

from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from tenants.permissions import TenantAccessPermission
from financial.models import Product, StockMovement, Comanda, CommandaItem, CashEntry
from agenda.models import Appointment, Professional


# ════════════════════════════════════════════════════════════════
# PRODUTOS
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def products_view(request):
    """
    GET  /api/financial/products/  → lista produtos
    POST /api/financial/products/  → cria produto
    """
    tenant = request.tenant

    if request.method == 'GET':
        products = Product.objects.filter(tenant=tenant, is_active=True)
        category = request.query_params.get('category')
        if category:
            products = products.filter(category=category)

        return Response([
            {
                'id':          str(p.id),
                'name':        p.name,
                'category':    p.category,
                'price':       float(p.price),
                'cost_price':  float(p.cost_price),
                'margin_pct':  p.margin_pct,
                'stock_qty':   p.stock_qty,
                'stock_alert': p.stock_alert,
                'track_stock': p.track_stock,
                'stock_low':   p.stock_low,
            }
            for p in products
        ])

    # POST
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    name  = request.data.get('name', '').strip()
    price = request.data.get('price')
    if not name or price is None:
        return Response({'error': 'name e price são obrigatórios.'}, status=400)

    product = Product.objects.create(
        tenant       = tenant,
        name         = name,
        category     = request.data.get('category', 'product'),
        price        = float(price),
        cost_price   = float(request.data.get('cost_price', 0)),
        stock_qty    = int(request.data.get('stock_qty', 0)),
        stock_alert  = int(request.data.get('stock_alert', 5)),
        track_stock  = request.data.get('track_stock', True),
    )

    return Response({
        'id':         str(product.id),
        'name':       product.name,
        'price':      float(product.price),
        'stock_qty':  product.stock_qty,
    }, status=201)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def product_detail_view(request, product_id):
    """CRUD de produto."""
    tenant = request.tenant
    try:
        product = Product.objects.get(id=product_id, tenant=tenant)
    except Product.DoesNotExist:
        return Response({'error': 'Produto não encontrado.'}, status=404)

    if request.method == 'GET':
        movements = StockMovement.objects.filter(product=product).order_by('-created_at')[:10]
        return Response({
            'id':          str(product.id),
            'name':        product.name,
            'category':    product.category,
            'price':       float(product.price),
            'cost_price':  float(product.cost_price),
            'margin_pct':  product.margin_pct,
            'stock_qty':   product.stock_qty,
            'stock_alert': product.stock_alert,
            'track_stock': product.track_stock,
            'stock_low':   product.stock_low,
            'movements': [
                {
                    'type':      m.type,
                    'quantity':  m.quantity,
                    'reason':    m.reason,
                    'created_at': m.created_at.isoformat(),
                }
                for m in movements
            ],
        })

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method == 'PATCH':
        for field in ['name', 'price', 'cost_price', 'stock_alert', 'track_stock', 'category']:
            if field in request.data:
                setattr(product, field, request.data[field])
        product.save()
        return Response({'message': 'Produto atualizado.'})

    if request.method == 'DELETE':
        product.is_active = False
        product.save(update_fields=['is_active'])
        return Response({'message': 'Produto desativado.'})


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def stock_movement_view(request, product_id):
    """
    POST /api/financial/products/{id}/stock/
    Entrada ou ajuste de estoque.
    Body: {"type": "in", "quantity": 10, "reason": "Compra fornecedor", "cost_price": 12.00}
    """
    tenant = request.tenant
    try:
        product = Product.objects.get(id=product_id, tenant=tenant)
    except Product.DoesNotExist:
        return Response({'error': 'Produto não encontrado.'}, status=404)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    mov_type = request.data.get('type', 'in')
    quantity = int(request.data.get('quantity', 0))
    reason   = request.data.get('reason', '')

    if quantity == 0:
        return Response({'error': 'quantity não pode ser zero.'}, status=400)

    # Saída → quantity negativo
    if mov_type == 'out':
        quantity = -abs(quantity)

    movement = StockMovement.objects.create(
        tenant     = tenant,
        product    = product,
        type       = mov_type,
        quantity   = quantity,
        reason     = reason,
        cost_price = request.data.get('cost_price'),
        created_by = request.user,
    )

    return Response({
        'message':       f"Estoque atualizado.",
        'stock_qty':     product.stock_qty,
        'movement_type': mov_type,
        'quantity':      abs(quantity),
    }, status=201)


@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def stock_alerts_view(request):
    """GET /api/financial/stock/alerts/ — produtos com estoque baixo"""
    tenant   = request.tenant
    products = Product.objects.filter(tenant=tenant, is_active=True, track_stock=True)

    alerts = [
        {
            'id':          str(p.id),
            'name':        p.name,
            'stock_qty':   p.stock_qty,
            'stock_alert': p.stock_alert,
        }
        for p in products if p.stock_low
    ]

    return Response({'alerts': alerts, 'total': len(alerts)})


# ════════════════════════════════════════════════════════════════
# COMANDA
# ════════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def comanda_view(request, appointment_id):
    """
    GET  /api/financial/appointments/{id}/comanda/ → abre/retorna comanda
    POST /api/financial/appointments/{id}/comanda/ → adiciona item
    """
    tenant = request.tenant

    try:
        appointment = Appointment.objects.get(id=appointment_id, tenant=tenant)
    except Appointment.DoesNotExist:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)

    if request.method == 'GET':
        # Cria comanda se não existe ainda
        comanda, created = Comanda.objects.get_or_create(
            appointment=appointment,
            defaults={'tenant': tenant}
        )

        # Se nova comanda, adiciona o serviço do agendamento automaticamente
        if created:
            commission_pct = appointment.professional.commission_pct if appointment.professional else 0
            CommandaItem.objects.create(
                comanda        = comanda,
                description    = appointment.service.name,
                quantity       = 1,
                unit_price     = appointment.price_snapshot or appointment.service.price,
                commission_pct = commission_pct,
            )

        return Response(_serialize_comanda(comanda))

    # POST — adiciona item
    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    try:
        comanda = Comanda.objects.get(appointment=appointment, tenant=tenant)
    except Comanda.DoesNotExist:
        return Response({'error': 'Abra a comanda primeiro (GET).'}, status=400)

    if comanda.status == Comanda.Status.CLOSED:
        return Response({'error': 'Comanda já foi fechada.'}, status=400)

    product_id  = request.data.get('product_id')
    description = request.data.get('description', '').strip()
    quantity    = int(request.data.get('quantity', 1))
    unit_price  = request.data.get('unit_price')
    discount    = float(request.data.get('discount', 0))
    is_courtesy = request.data.get('is_courtesy', False)

    product = None
    if product_id:
        try:
            product      = Product.objects.get(id=product_id, tenant=tenant, is_active=True)
            description  = description or product.name
            unit_price   = unit_price or float(product.price)
        except Product.DoesNotExist:
            return Response({'error': 'Produto não encontrado.'}, status=404)

    if not description:
        return Response({'error': 'description ou product_id obrigatório.'}, status=400)
    if not unit_price:
        return Response({'error': 'unit_price obrigatório.'}, status=400)

    commission_pct = float(request.data.get(
        'commission_pct',
        appointment.professional.commission_pct if appointment.professional else 0
    ))

    item = CommandaItem.objects.create(
        comanda        = comanda,
        product        = product,
        description    = description,
        quantity       = quantity,
        unit_price     = float(unit_price),
        discount       = discount,
        is_courtesy    = is_courtesy,
        commission_pct = commission_pct,
    )

    # Desconta estoque se produto com track_stock
    if product and product.track_stock:
        StockMovement.objects.create(
            tenant     = tenant,
            product    = product,
            type       = StockMovement.Type.OUT,
            quantity   = -quantity,
            reason     = f"Venda na comanda #{str(comanda.id)[:8]}",
            created_by = request.user,
        )

    return Response({
        'message': 'Item adicionado.',
        'item': _serialize_item(item),
        'comanda_total': comanda.total,
    }, status=201)


@api_view(['PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def comanda_item_view(request, item_id):
    """
    PATCH  /api/financial/comanda/items/{id}/ → edita item
    DELETE /api/financial/comanda/items/{id}/ → remove item
    """
    tenant = request.tenant

    try:
        item = CommandaItem.objects.select_related('comanda__tenant').get(
            id=item_id, comanda__tenant=tenant
        )
    except CommandaItem.DoesNotExist:
        return Response({'error': 'Item não encontrado.'}, status=404)

    if item.comanda.status == Comanda.Status.CLOSED:
        return Response({'error': 'Comanda fechada.'}, status=400)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method == 'PATCH':
        for field in ['quantity', 'unit_price', 'discount', 'is_courtesy', 'commission_pct']:
            if field in request.data:
                setattr(item, field, request.data[field])
        item.save()
        return Response({'message': 'Item atualizado.', 'item': _serialize_item(item)})

    if request.method == 'DELETE':
        # Devolve ao estoque se produto
        if item.product and item.product.track_stock:
            StockMovement.objects.create(
                tenant     = tenant,
                product    = item.product,
                type       = StockMovement.Type.IN,
                quantity   = item.quantity,
                reason     = "Remoção de item da comanda",
                created_by = request.user,
            )
        item.delete()
        return Response({'message': 'Item removido.'})


@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def comanda_checkout_view(request, appointment_id):
    """
    POST /api/financial/appointments/{id}/checkout/
    Fecha comanda + gera CashEntry + marca appointment como completed.

    Body: {"payment_method": "pix"}
    """
    tenant = request.tenant

    try:
        appointment = Appointment.objects.get(id=appointment_id, tenant=tenant)
    except Appointment.DoesNotExist:
        return Response({'error': 'Agendamento não encontrado.'}, status=404)

    if appointment.status not in ('confirmed', 'in_comanda'):
        return Response({
            'error': f"Agendamento com status '{appointment.get_status_display()}' não pode ser finalizado."
        }, status=400)

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    # Busca ou cria comanda
    comanda, created = Comanda.objects.get_or_create(
        appointment=appointment,
        defaults={'tenant': tenant}
    )

    if created:
        # Comanda nova — adiciona serviço automaticamente
        commission_pct = appointment.professional.commission_pct if appointment.professional else 0
        CommandaItem.objects.create(
            comanda        = comanda,
            description    = appointment.service.name,
            quantity       = 1,
            unit_price     = appointment.price_snapshot or appointment.service.price,
            commission_pct = commission_pct,
        )

    if comanda.status == Comanda.Status.CLOSED:
        return Response({'error': 'Comanda já foi fechada.'}, status=400)

    payment_method = request.data.get('payment_method', 'pix')
    total          = comanda.total
    commission     = comanda.total_commission

    # Fecha comanda
    comanda.status    = Comanda.Status.CLOSED
    comanda.closed_at = timezone.now()
    comanda.save(update_fields=['status', 'closed_at'])

    # Cria CashEntry
    cash_entry = CashEntry.objects.create(
        tenant            = tenant,
        appointment       = appointment,
        comanda           = comanda,
        professional      = appointment.professional,
        amount            = total,
        commission_amount = commission,
        payment_method    = payment_method,
    )

    # Marca appointment como completed
    appointment.status         = Appointment.Status.COMPLETED
    appointment.price_snapshot = total
    appointment.save(update_fields=['status', 'price_snapshot', 'updated_at'])

    # Atualiza perfil do cliente
    if appointment.client:
        try:
            from clients.models import ClientTenantProfile
            profile, _ = ClientTenantProfile.objects.get_or_create(
                client=appointment.client, tenant=tenant
            )
            profile.last_visit_at  = timezone.now()
            profile.total_visits  += 1
            profile.save(update_fields=['last_visit_at', 'total_visits'])
        except Exception:
            pass

    return Response({
        'message':         'Atendimento finalizado.',
        'appointment_id':  str(appointment.id),
        'status':          appointment.status,
        'total':           float(total),
        'commission':      float(commission),
        'payment_method':  payment_method,
        'comanda':         _serialize_comanda(comanda),
    })


# ════════════════════════════════════════════════════════════════
# CAIXA DO DIA
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def cashbox_view(request):
    """
    GET /api/financial/cashbox/
    ?date=2026-05-23  (padrão: hoje)
    """
    tenant   = request.tenant
    date_str = request.query_params.get('date', date.today().isoformat())

    try:
        filter_date = date.fromisoformat(date_str)
    except ValueError:
        return Response({'error': 'date inválido.'}, status=400)

    entries = CashEntry.objects.filter(
        tenant=tenant,
        created_at__date=filter_date,
    ).select_related('professional', 'appointment__service')

    total_revenue = entries.aggregate(total=Sum('amount'))['total'] or 0
    total_commission = entries.aggregate(total=Sum('commission_amount'))['total'] or 0

    # Por forma de pagamento
    by_payment = {}
    for entry in entries:
        pm = entry.payment_method
        by_payment[pm] = by_payment.get(pm, 0) + float(entry.amount)

    # Por profissional
    by_professional = {}
    for entry in entries:
        if entry.professional:
            name = entry.professional.name
            if name not in by_professional:
                by_professional[name] = {'revenue': 0, 'appointments': 0, 'commission': 0}
            by_professional[name]['revenue']      += float(entry.amount)
            by_professional[name]['appointments'] += 1
            by_professional[name]['commission']   += float(entry.commission_amount)

    # Agendamentos do dia
    appointments = Appointment.objects.filter(
        tenant=tenant, starts_at__date=filter_date
    ).exclude(status='cancelled')

    total_appts     = appointments.count()
    completed_appts = appointments.filter(status='completed').count()
    pending_appts   = appointments.filter(status__in=['pending', 'confirmed', 'in_comanda']).count()

    return Response({
        'date':              date_str,
        'total_revenue':     float(total_revenue),
        'total_commission':  float(total_commission),
        'avg_ticket':        round(float(total_revenue) / completed_appts, 2) if completed_appts else 0,
        'appointments': {
            'total':     total_appts,
            'completed': completed_appts,
            'pending':   pending_appts,
        },
        'by_payment':      by_payment,
        'by_professional': [
            {'name': name, **data}
            for name, data in sorted(by_professional.items(), key=lambda x: -x[1]['revenue'])
        ],
    })


# ════════════════════════════════════════════════════════════════
# RELATÓRIO MENSAL
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def report_monthly_view(request):
    """
    GET /api/financial/report/monthly/
    ?year=2026&month=5  (padrão: mês atual)
    """
    tenant = request.tenant
    today  = date.today()
    year   = int(request.query_params.get('year', today.year))
    month  = int(request.query_params.get('month', today.month))

    from calendar import monthrange
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end   = date(year, month, last_day)

    entries = CashEntry.objects.filter(
        tenant=tenant,
        created_at__date__gte=month_start,
        created_at__date__lte=month_end,
    ).select_related('professional', 'appointment__service')

    total_revenue    = sum(float(e.amount) for e in entries)
    total_commission = sum(float(e.commission_amount) for e in entries)
    total_appts      = Appointment.objects.filter(
        tenant=tenant,
        starts_at__date__gte=month_start,
        starts_at__date__lte=month_end,
        status='completed'
    ).count()

    # Por semana
    by_week = {}
    for entry in entries:
        week = entry.created_at.isocalendar()[1]
        by_week[week] = by_week.get(week, 0) + float(entry.amount)

    # Por profissional
    by_professional = {}
    for entry in entries:
        if entry.professional:
            name = entry.professional.name
            if name not in by_professional:
                by_professional[name] = {'revenue': 0, 'appointments': 0, 'commission': 0}
            by_professional[name]['revenue']      += float(entry.amount)
            by_professional[name]['appointments'] += 1
            by_professional[name]['commission']   += float(entry.commission_amount)

    # Por serviço
    by_service = {}
    for entry in entries:
        if entry.appointment and entry.appointment.service:
            name = entry.appointment.service.name
            if name not in by_service:
                by_service[name] = {'revenue': 0, 'count': 0}
            by_service[name]['revenue'] += float(entry.amount)
            by_service[name]['count']   += 1

    # Por forma de pagamento
    by_payment = {}
    for entry in entries:
        pm = entry.payment_method
        by_payment[pm] = by_payment.get(pm, 0) + float(entry.amount)

    # Melhor dia
    by_day = {}
    for entry in entries:
        d = entry.created_at.date().isoformat()
        by_day[d] = by_day.get(d, 0) + float(entry.amount)
    best_day = max(by_day.items(), key=lambda x: x[1]) if by_day else None

    return Response({
        'year':  year,
        'month': month,
        'period': f"{month_start.isoformat()} a {month_end.isoformat()}",
        'summary': {
            'total_revenue':    round(total_revenue, 2),
            'total_commission': round(total_commission, 2),
            'total_appointments': total_appts,
            'avg_ticket':       round(total_revenue / total_appts, 2) if total_appts else 0,
            'best_day':         {'date': best_day[0], 'revenue': best_day[1]} if best_day else None,
        },
        'by_week':         [{'week': w, 'revenue': r} for w, r in sorted(by_week.items())],
        'by_professional': [{'name': n, **d} for n, d in sorted(by_professional.items(), key=lambda x: -x[1]['revenue'])],
        'by_service':      [{'name': n, **d} for n, d in sorted(by_service.items(), key=lambda x: -x[1]['revenue'])],
        'by_payment':      by_payment,
    })


# ════════════════════════════════════════════════════════════════
# COMISSÕES
# ════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def commissions_view(request):
    """
    GET /api/financial/commissions/
    ?year=2026&month=5  (padrão: mês atual)
    """
    tenant = request.tenant
    today  = date.today()
    year   = int(request.query_params.get('year', today.year))
    month  = int(request.query_params.get('month', today.month))

    from calendar import monthrange
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end   = date(year, month, last_day)

    entries = CashEntry.objects.filter(
        tenant=tenant,
        created_at__date__gte=month_start,
        created_at__date__lte=month_end,
        professional__isnull=False,
    ).select_related('professional')

    by_professional = {}
    for entry in entries:
        prof = entry.professional
        pid  = str(prof.id)
        if pid not in by_professional:
            by_professional[pid] = {
                'professional_id':   pid,
                'name':              prof.name,
                'commission_pct':    float(prof.commission_pct),
                'revenue_generated': 0,
                'commission_total':  0,
                'appointments':      0,
            }
        by_professional[pid]['revenue_generated'] += float(entry.amount)
        by_professional[pid]['commission_total']  += float(entry.commission_amount)
        by_professional[pid]['appointments']      += 1

    result = sorted(by_professional.values(), key=lambda x: -x['commission_total'])
    total  = sum(p['commission_total'] for p in result)

    return Response({
        'year':          year,
        'month':         month,
        'period':        f"{month_start.isoformat()} a {month_end.isoformat()}",
        'total_to_pay':  round(total, 2),
        'professionals': result,
    })


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def _serialize_item(item):
    return {
        'id':             str(item.id),
        'description':    item.description,
        'quantity':       item.quantity,
        'unit_price':     float(item.unit_price),
        'discount':       float(item.discount),
        'is_courtesy':    item.is_courtesy,
        'commission_pct': float(item.commission_pct),
        'total':          item.total,
        'commission_value': item.commission_value,
        'product_id':     str(item.product.id) if item.product else None,
    }


def _serialize_comanda(comanda):
    return {
        'id':             str(comanda.id),
        'status':         comanda.status,
        'opened_at':      comanda.opened_at.isoformat(),
        'closed_at':      comanda.closed_at.isoformat() if comanda.closed_at else None,
        'subtotal':       comanda.subtotal,
        'total_discount': comanda.total_discount,
        'total':          comanda.total,
        'total_commission': comanda.total_commission,
        'items':          [_serialize_item(i) for i in comanda.items.all()],
        'notes':          comanda.notes,
    }