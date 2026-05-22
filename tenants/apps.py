# tenants/apps.py

from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'tenants'
    verbose_name       = 'Estabelecimentos'

    def ready(self):
        """
        Iniciado quando o Django sobe.
        Não inicia o scheduler em modo de migrate/shell/test.
        """
        import sys

        # Só inicia em runserver / gunicorn — não em migrate, shell, test
        is_manage_command = any(
            cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'shell', 'test', 'collectstatic']
        )

        if not is_manage_command:
            from tenants import scheduler
            scheduler.start()