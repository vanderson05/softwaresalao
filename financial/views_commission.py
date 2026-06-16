# financial/views_commission.py
# Geração de comissões usando CommissionEntry como base

from datetime import date, timedelta
from calendar import monthrange
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from tenants.permissions import TenantAccessPermission
from financial.models import CommissionEntry, AccountsPayable, Expense
from agenda.models import Professional


FREQUENCY_LABELS = {
    'daily':    'Diário',
    'weekly':   'Semanal',
    'biweekly': 'Quinzenal',
    'monthly':  'Mensal',
}


def _to_date(value) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _get_periods(frequency: str, ref_date: date):
    """Retorna (period_start, period_end, due_date) para a frequência."""
    if frequency == 'daily':
        return [(ref_date, ref_date, ref_date)]

    if frequency == 'weekly':
        weekday    = ref_date.weekday()
        week_start = ref_date - timedelta(days=weekday)
        week_end   = week_start + timedelta(days=6)
        due        = week_end + timedelta(days=1)
        return [(week_start, week_end, due)]

    if frequency == 'biweekly':
        y, m = ref_date.year, ref_date.month
        _, last = monthrange(y, m)
        if ref_date.day <= 15:
            return [(date(y, m, 1), date(y, m, 15), date(y, m, 16))]
        else:
            from dateutil.relativedelta import relativedelta
            next_m = date(y, m, 16) + relativedelta(months=1)
            return [(date(y, m, 16), date(y, m, last),
                     date(next_m.year, next_m.month, 1))]

    # monthly (default)
    y, m = ref_date.year, ref_date.month
    _, last = monthrange(y, m)
    from dateutil.relativedelta import relativedelta
    due = date(y, m, 1) + relativedelta(months=1)
    due = due.replace(day=5)
    return [(date(y, m, 1), date(y, m, last), due)]


def _already_generated(tenant, professional, period_start, period_end) -> bool:
    desc_prefix = f"Comissão {professional.name}"
    return AccountsPayable.objects.filter(
        tenant=tenant,
        category='commission',
        description__startswith=desc_prefix,
        due_date__gte=period_start,
        due_date__lte=period_end + timedelta(days=10),
    ).exists()


def _serialize_payable(p):
    today = date.today()
    due   = _to_date(p.due_date)
    is_overdue = p.status == 'pending' and due < today
    return {
        'id':          str(p.id),
        'description': p.description,
        'amount':      float(p.amount),
        'due_date':    due.isoformat(),
        'status':      'overdue' if is_overdue else p.status,
        'paid_at':     p.paid_at.isoformat() if p.paid_at else None,
        'paid_amount': float(p.paid_amount) if p.paid_amount else None,
        'days_until':  (due - today).days,
        'notes':       p.notes,
    }


# ── Lista pagamentos de comissão ──────────────────────────────

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def commission_payables_view(request):
    """GET /api/financial/commission-payables/"""
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    payables = AccountsPayable.objects.filter(
        tenant=tenant,
        category='commission',
    ).order_by('due_date')

    today         = date.today()
    total_pending = sum(float(p.amount) for p in payables if p.status == 'pending')
    total_paid    = sum(float(p.paid_amount or p.amount) for p in payables if p.status == 'paid')

    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    prof_config   = [{
        'id':                   str(p.id),
        'name':                 p.name,
        'commission_pct':       float(p.commission_pct),
        'commission_frequency': getattr(p, 'commission_frequency', 'monthly'),
        'frequency_label':      FREQUENCY_LABELS.get(getattr(p, 'commission_frequency', 'monthly'), 'Mensal'),
    } for p in professionals]

    return Response({
        'payables':      [_serialize_payable(p) for p in payables],
        'professionals': prof_config,
        'summary': {
            'total_pending': round(total_pending, 2),
            'total_paid':    round(total_paid, 2),
        },
    })


# ── Extrato de comissões por profissional ─────────────────────

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def commission_entries_view(request):
    """
    GET /api/financial/commission-entries/
    ?professional_id=uuid&year=2026&month=6

    Retorna o extrato detalhado de comissões por serviço.
    """
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    today = date.today()
    year  = int(request.query_params.get('year',  today.year))
    month = int(request.query_params.get('month', today.month))
    prof_id = request.query_params.get('professional_id')

    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end   = date(year, month, last_day)

    qs = CommissionEntry.objects.filter(
        tenant=tenant,
        service_date__gte=month_start,
        service_date__lte=month_end,
    ).select_related('professional', 'appointment')

    if prof_id:
        qs = qs.filter(professional_id=prof_id)

    # Agrupa por profissional
    by_prof: dict = {}
    for entry in qs:
        pid  = str(entry.professional_id) if entry.professional else 'none'
        name = entry.professional_name
        if pid not in by_prof:
            by_prof[pid] = {
                'professional_id':   pid,
                'name':              name,
                'commission_pct':    float(entry.commission_pct),
                'total_service':     0.0,
                'total_commission':  0.0,
                'appointments':      0,
                'entries':           [],
            }
        by_prof[pid]['total_service']    += float(entry.service_price)
        by_prof[pid]['total_commission'] += float(entry.commission_amount)
        by_prof[pid]['appointments']     += 1
        by_prof[pid]['entries'].append({
            'id':               str(entry.id),
            'service_name':     entry.service_name,
            'service_price':    float(entry.service_price),
            'commission_pct':   float(entry.commission_pct),
            'commission_amount':float(entry.commission_amount),
            'payment_method':   entry.payment_method,
            'client_name':      entry.client_name,
            'client_phone':     entry.client_phone,
            'service_date':     entry.service_date.isoformat(),
            'service_time':     str(entry.service_time)[:5],
            'is_paid':          entry.is_paid,
        })

    result = sorted(by_prof.values(), key=lambda x: -x['total_commission'])
    total  = sum(p['total_commission'] for p in result)

    return Response({
        'year':          year,
        'month':         month,
        'total_to_pay':  round(total, 2),
        'professionals': result,
    })


# ── Gerar pagamentos de comissão ──────────────────────────────

@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def generate_commission_payables_view(request):
    """
    POST /api/financial/commission-payables/generate/
    Usa CommissionEntry como base — calcula só sobre serviços.
    """
    tenant = request.tenant

    if request.tenant_role != 'owner':
        return Response({'error': 'Apenas o dono pode gerar pagamentos.'}, status=403)

    ref_date_str     = request.data.get('ref_date', date.today().isoformat())
    professional_ids = request.data.get('professional_ids', [])
    force            = request.data.get('force', False)

    try:
        ref_date = date.fromisoformat(ref_date_str)
    except ValueError:
        return Response({'error': 'ref_date inválido.'}, status=400)

    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    if professional_ids:
        professionals = professionals.filter(id__in=professional_ids)

    generated = []
    skipped   = []

    for prof in professionals:
        frequency = getattr(prof, 'commission_frequency', 'monthly')
        periods   = _get_periods(frequency, ref_date)

        for period_start, period_end, due_date in periods:
            if not force and _already_generated(tenant, prof, period_start, period_end):
                skipped.append({
                    'professional': prof.name,
                    'period':       f"{period_start} a {period_end}",
                    'reason':       'Já gerado para este período',
                })
                continue

            # Soma APENAS das CommissionEntries (só serviços)
            entries = CommissionEntry.objects.filter(
                tenant=tenant,
                professional=prof,
                service_date__gte=period_start,
                service_date__lte=period_end,
                is_paid=False,
            )

            amount = round(sum(float(e.commission_amount) for e in entries), 2)

            if amount <= 0:
                skipped.append({
                    'professional': prof.name,
                    'period':       f"{period_start} a {period_end}",
                    'reason':       'Sem comissões no período (R$0,00)',
                })
                continue

            freq_label  = FREQUENCY_LABELS.get(frequency, 'Mensal')
            description = (
                f"Comissão {prof.name} — {freq_label} "
                f"({period_start.strftime('%d/%m')} a {period_end.strftime('%d/%m/%Y')})"
            )

            # Detalhe das entradas no notes
            detail_lines = [
                f"  {e.service_date} {str(e.service_time)[:5]} | "
                f"{e.service_name} R${e.service_price} × {e.commission_pct}% "
                f"= R${e.commission_amount} | {e.client_name or e.client_phone}"
                for e in entries
            ]
            notes = f"Período: {period_start} a {period_end}\n" + "\n".join(detail_lines)

            payable = AccountsPayable.objects.create(
                tenant      = tenant,
                description = description,
                category    = 'commission',
                amount      = amount,
                due_date    = due_date,
                recurrence  = 'once',
                notes       = notes,
                created_by  = request.user,
            )

            # Vincula as entries ao payable
            entries.update(payable=payable)

            generated.append({
                'id':           str(payable.id),
                'professional': prof.name,
                'amount':       amount,
                'entries':      entries.count(),
                'period':       f"{period_start} a {period_end}",
                'due_date':     due_date.isoformat(),
                'frequency':    freq_label,
            })

    return Response({
        'message':   f'{len(generated)} pagamento(s) gerado(s).',
        'generated': generated,
        'skipped':   skipped,
    }, status=201 if generated else 200)


# ── Marcar comissões como pagas ───────────────────────────────

@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def pay_commission_payable_view(request, payable_id):
    """
    POST /api/financial/commission-payables/{id}/pay/
    Marca comissão como paga → cria Expense → marca CommissionEntries como pagas.
    """
    tenant = request.tenant

    if request.tenant_role != 'owner':
        return Response({'error': 'Sem permissão.'}, status=403)

    try:
        payable = AccountsPayable.objects.get(
            id=payable_id, tenant=tenant, category='commission'
        )
    except AccountsPayable.DoesNotExist:
        return Response({'error': 'Conta não encontrada.'}, status=404)

    if payable.status == AccountsPayable.Status.PAID:
        return Response({'error': 'Já foi pago.'}, status=400)

    paid_amount = float(request.data.get('paid_amount', payable.amount))

    # Marca payable como pago
    payable.status      = AccountsPayable.Status.PAID
    payable.paid_at     = timezone.now()
    payable.paid_amount = paid_amount
    payable.save()

    # Cria Expense (comissão agora é despesa real)
    Expense.objects.create(
        tenant      = tenant,
        description = payable.description,
        amount      = paid_amount,
        category    = 'commission',
        date        = date.today(),
        notes       = f'Comissão paga — {payable.description}',
        created_by  = request.user,
    )

    # Marca CommissionEntries vinculadas como pagas
    CommissionEntry.objects.filter(
        payable=payable
    ).update(is_paid=True, paid_at=timezone.now())

    return Response({
        'message': f'Comissão de {paid_amount} paga com sucesso.',
        'payable': _serialize_payable(payable),
    })