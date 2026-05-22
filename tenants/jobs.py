# tenants/jobs.py
# Jobs agendados relacionados ao trial
# Chamados pelo APScheduler via tenants/scheduler.py

from django.utils import timezone
from django.db.models import Q


def check_trial_expiry():
    """
    Roda diariamente às 9h.
    Verifica tenants em trial e:
    - Dia 10: envia aviso "expira em 4 dias"
    - Dia 13: envia aviso urgente "expira amanhã"
    - Dia 14+: bloqueia acesso (is_active=False)
    """
    from tenants.models import Tenant, Plan
    from tenants.emails import send_trial_expiry_warning

    now   = timezone.now()
    hoje  = now.date()

    # Busca todos os tenants em trial ainda ativos
    tenants_trial = Tenant.objects.filter(
        plan      = Plan.TRIAL,
        is_active = True,
    )

    bloqueados  = 0
    avisos_4d   = 0
    avisos_1d   = 0

    for tenant in tenants_trial:
        if not tenant.trial_ends_at:
            continue

        dias_restantes = tenant.trial_days_remaining
        trial_end_date = tenant.trial_ends_at.date()

        # Trial expirado — bloqueia acesso
        if now >= tenant.trial_ends_at:
            tenant.is_active = False
            tenant.save(update_fields=['is_active'])
            bloqueados += 1
            print(f"[TRIAL] Bloqueado: {tenant.name} ({tenant.slug})")
            continue

        # Aviso 4 dias antes (dia 10 do trial)
        if dias_restantes == 4:
            try:
                send_trial_expiry_warning(tenant, dias_restantes)
                avisos_4d += 1
                print(f"[TRIAL] Aviso 4 dias: {tenant.name}")
            except Exception as e:
                print(f"[TRIAL] Erro ao enviar aviso: {e}")

        # Aviso 1 dia antes (dia 13 do trial)
        elif dias_restantes == 1:
            try:
                send_trial_expiry_warning(tenant, dias_restantes)
                avisos_1d += 1
                print(f"[TRIAL] Aviso 1 dia: {tenant.name}")
            except Exception as e:
                print(f"[TRIAL] Erro ao enviar aviso: {e}")

    print(f"[TRIAL] Resultado: {bloqueados} bloqueados, {avisos_4d} avisos 4d, {avisos_1d} avisos 1d")
    return {
        'bloqueados': bloqueados,
        'avisos_4d':  avisos_4d,
        'avisos_1d':  avisos_1d,
    }


def delete_expired_tenants():
    """
    Roda semanalmente (domingo às 3h).
    Deleta tenants inativos há mais de 30 dias.
    Preserva dados por 30 dias após bloqueio antes de deletar.
    """
    from tenants.models import Tenant, Plan

    limite = timezone.now() - timezone.timedelta(days=30)

    tenants_expirados = Tenant.objects.filter(
        plan          = Plan.TRIAL,
        is_active     = False,
        trial_ends_at__lt = limite,
    )

    total = tenants_expirados.count()

    for tenant in tenants_expirados:
        print(f"[CLEANUP] Deletando: {tenant.name} ({tenant.slug})")
        tenant.delete()

    print(f"[CLEANUP] {total} tenant(s) deletado(s)")
    return {'deletados': total}