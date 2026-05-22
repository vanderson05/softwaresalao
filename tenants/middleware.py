# tenants/middleware.py

from django.http import Http404
from tenants.models import Tenant


class TenantMiddleware:
    """
    Identifica o tenant pela request.
    Suporta 3 formas:
    1. Subdomínio: carlao.beautiapp.com.br
    2. Header X-Tenant-Slug: carlao (para testes e apps mobile)
    3. Rotas de webhook: tenant resolvido na própria view
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Webhook WhatsApp — a view resolve o tenant pelo phone_number_id
        if request.path.startswith('/api/webhook/'):
            request.tenant = None
            return self.get_response(request)

        # Rotas públicas — não precisam de tenant
        PUBLIC_PATHS = [
            '/admin/',
            '/api/auth/register/',
            '/api/auth/login/',
            '/api/auth/verify/',
            '/api/auth/resend-verification/',
            '/api/token/refresh/',
        ]
        if any(request.path.startswith(p) for p in PUBLIC_PATHS):
            request.tenant = None
            return self.get_response(request)

        tenant = None

        # 1. Header explícito (Postman / app mobile / testes)
        slug = request.headers.get('X-Tenant-Slug')
        if slug:
            try:
                tenant = Tenant.objects.get(slug=slug, is_active=True)
            except Tenant.DoesNotExist:
                raise Http404(f"Estabelecimento '{slug}' não encontrado.")

        # 2. Subdomínio (painel web)
        if not tenant:
            host  = request.get_host().split(':')[0]
            parts = host.split('.')
            # carlao.beautiapp.com.br → ['carlao', 'beautiapp', 'com', 'br']
            if len(parts) >= 3 and 'beautiapp' in parts:
                idx  = parts.index('beautiapp')
                slug = parts[idx - 1] if idx > 0 else None
                if slug and slug not in ('www', 'admin', 'api'):
                    try:
                        tenant = Tenant.objects.get(slug=slug, is_active=True)
                    except Tenant.DoesNotExist:
                        raise Http404(f"Estabelecimento '{slug}' não encontrado.")

        request.tenant = tenant
        return self.get_response(request)