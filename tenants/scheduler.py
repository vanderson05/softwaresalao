# tenants/scheduler.py
# Configura e inicia o APScheduler
# Iniciado automaticamente pelo AppConfig (tenants/apps.py)

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings

scheduler = None


def start():
    global scheduler

    if scheduler and scheduler.running:
        return

    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

    # Verifica trial todo dia às 9h (horário de Brasília)
    scheduler.add_job(
        func     = 'tenants.jobs:check_trial_expiry',
        trigger  = CronTrigger(hour=9, minute=0),
        id       = 'check_trial_expiry',
        name     = 'Verificar expiração de trial',
        replace_existing = True,
    )

    # Deleta tenants expirados todo domingo às 3h
    scheduler.add_job(
        func     = 'tenants.jobs:delete_expired_tenants',
        trigger  = CronTrigger(day_of_week='sun', hour=3, minute=0),
        id       = 'delete_expired_tenants',
        name     = 'Deletar tenants expirados',
        replace_existing = True,
    )

    scheduler.start()
    print("[SCHEDULER] Iniciado — jobs: check_trial_expiry, delete_expired_tenants")


def stop():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("[SCHEDULER] Parado")