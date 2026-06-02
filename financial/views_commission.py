# financial/views_commission.py
# Geração automática de comissões como Contas a Pagar

from datetime import date, timedelta
from calendar import monthrange
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from tenants.permissions import TenantAccessPermission
from financial.models import CashEntry, AccountsPayable, Expense
from agenda.models import Professional


FREQUENCY_LABELS = {
    'daily':    'Diário',
    'weekly':   'Semanal',
    'biweekly': 'Quinzenal',
    'monthly':  'Mensal',
}


def _get_periods(frequency: str, ref_date: date) -> list[tuple[date, date, date]]:
    """
    Retorna lista de (period_start, period_end, due_date) para a frequência.
    ref_date = data de referência (geralmente hoje ou data solicitada).
    """
    periods = []

    if frequency == 'daily':
        # Cada dia é um período, vencimento = mesmo dia
        d = ref_date
        periods.append((d, d, d))

    elif frequency == 'weekly':
        # Semana atual: segunda a domingo, vencimento = próxima segunda
        weekday   = ref_date.weekday()  # 0=segunda
        week_start= ref_date - timedelta(days=weekday)
        week_end  = week_start + timedelta(days=6)
        due       = week_end + timedelta(days=1)  # segunda seguinte
        periods.append((week_start, week_end, due))

    elif frequency == 'biweekly':
        # Quinzena 1: dias 1-15, vencimento dia 16
        # Quinzena 2: dias 16-fim, vencimento dia 1 do mês seguinte
        y, m = ref_date.year, ref_date.month
        _, last = monthrange(y, m)
        if ref_date.day <= 15:
            periods.append((date(y, m, 1), date(y, m, 15), date(y, m, 16)))
        else:
            next_month = date(y, m, 1) + timedelta(days=32)
            periods.append((date(y, m, 16), date(y, m, last), date(next_month.year, next_month.month, 1)))

    elif frequency == 'monthly':
        # Mês inteiro, vencimento dia 5 do mês seguinte
        y, m = ref_date.year, ref_date.month
        _, last = monthrange(y, m)
        next_month = date(y, m, 1) + timedelta(days=32)
        due = date(next_month.year, next_month.month, 5)
        periods.append((date(y, m, 1), date(y, m, last), due))

    return periods


def _calc_commission(tenant, professional: Professional,
                     period_start: date, period_end: date) -> float:
    """Soma comissões de um profissional em um período."""
    entries = CashEntry.objects.filter(
        tenant=tenant,
        professional=professional,
        created_at__date__gte=period_start,
        created_at__date__lte=period_end,
    )
    return round(sum(float(e.commission_amount) for e in entries), 2)


def _already_generated(tenant, professional: Professional,
                        period_start: date, period_end: date) -> bool:
    """Verifica se já foi gerada conta a pagar para este período."""
    desc_prefix = f"Comissão {professional.name}"
    return AccountsPayable.objects.filter(
        tenant=tenant,
        category='commission',
        description__startswith=desc_prefix,
        due_date__gte=period_start,
        due_date__lte=period_end + timedelta(days=10),
    ).exists()


# ── Lista pagamentos de comissão gerados ──────────────────────

@api_view(['GET'])
@permission_classes([TenantAccessPermission])
def commission_payables_view(request):
    """
    GET /api/financial/commission-payables/
    Lista as contas a pagar de comissão geradas.
    """
    tenant = request.tenant

    if request.tenant_role not in ('owner', 'manager'):
        return Response({'error': 'Sem permissão.'}, status=403)

    payables = AccountsPayable.objects.filter(
        tenant=tenant,
        category='commission',
    ).order_by('due_date')

    today = date.today()

    def serialize(p):
        due = p.due_date if isinstance(p.due_date, date) else date.fromisoformat(str(p.due_date))
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

    total_pending = sum(
        float(p.amount) for p in payables if p.status == 'pending'
    )
    total_paid = sum(
        float(p.paid_amount or p.amount) for p in payables if p.status == 'paid'
    )

    # Profissionais com frequência configurada
    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    prof_config   = [
        {
            'id':                   str(p.id),
            'name':                 p.name,
            'commission_pct':       float(p.commission_pct),
            'commission_frequency': getattr(p, 'commission_frequency', 'monthly'),
            'frequency_label':      FREQUENCY_LABELS.get(getattr(p, 'commission_frequency', 'monthly'), 'Mensal'),
        }
        for p in professionals
    ]

    return Response({
        'payables':      [serialize(p) for p in payables],
        'professionals': prof_config,
        'summary': {
            'total_pending': round(total_pending, 2),
            'total_paid':    round(total_paid, 2),
        },
    })


# ── Gerar pagamentos de comissão ──────────────────────────────

@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def generate_commission_payables_view(request):
    """
    POST /api/financial/commission-payables/generate/
    Calcula e gera AccountsPayable de comissão para um período.

    Body: {
        "ref_date":        "2026-06-01",  (opcional, default: hoje)
        "professional_ids": ["uuid1", "uuid2"],  (opcional, default: todos)
        "force":           false  (forçar regerar mesmo se já existe)
    }
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
        return Response({'error': 'ref_date inválido. Use YYYY-MM-DD.'}, status=400)

    # Profissionais
    professionals = Professional.objects.filter(tenant=tenant, is_active=True)
    if professional_ids:
        professionals = professionals.filter(id__in=professional_ids)

    generated = []
    skipped   = []
    errors    = []

    for prof in professionals:
        frequency = getattr(prof, 'commission_frequency', 'monthly')
        periods   = _get_periods(frequency, ref_date)

        for period_start, period_end, due_date in periods:
            # Verifica se já foi gerado
            if not force and _already_generated(tenant, prof, period_start, period_end):
                skipped.append({
                    'professional': prof.name,
                    'period':       f"{period_start} a {period_end}",
                    'reason':       'Já gerado para este período',
                })
                continue

            # Calcula comissão do período
            amount = _calc_commission(tenant, prof, period_start, period_end)

            if amount <= 0:
                skipped.append({
                    'professional': prof.name,
                    'period':       f"{period_start} a {period_end}",
                    'reason':       'Sem atendimentos no período (R$0,00)',
                })
                continue

            # Cria AccountsPayable
            freq_label = FREQUENCY_LABELS.get(frequency, 'Mensal')
            description = f"Comissão {prof.name} — {freq_label} ({period_start.strftime('%d/%m')} a {period_end.strftime('%d/%m/%Y')})"

            payable = AccountsPayable.objects.create(
                tenant      = tenant,
                description = description,
                category    = 'commission',
                amount      = amount,
                due_date    = due_date,
                recurrence  = 'once',
                notes       = f"Gerado automaticamente. Período: {period_start} a {period_end}. Profissional: {prof.name} ({prof.commission_pct}%)",
                created_by  = request.user,
            )

            generated.append({
                'id':           str(payable.id),
                'professional': prof.name,
                'amount':       amount,
                'period':       f"{period_start} a {period_end}",
                'due_date':     due_date.isoformat(),
                'frequency':    freq_label,
            })

    return Response({
        'message':   f'{len(generated)} pagamento(s) gerado(s).',
        'generated': generated,
        'skipped':   skipped,
        'errors':    errors,
    }, status=201 if generated else 200)