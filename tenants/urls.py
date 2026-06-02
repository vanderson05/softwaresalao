# ═══════════════════════════════════════════════════════════════
# apps/tenants/urls.py
# ═══════════════════════════════════════════════════════════════

from django.urls import path
from . import views
from .views_trial import trial_status_view, plans_view
from .views_setup import (
    setup_establishment_view,
    setup_status_view,
    setup_complete_view,
)
from tenants.views_team import team_view, team_member_view, team_link_professional
 
urlpatterns = [
    path('auth/register/',             views.register_view,            name='register'),
    path('auth/login/',                views.login_view,               name='login'),
    path('auth/verify/',               views.verify_email_view,        name='verify-email'),
    path('auth/resend-verification/',  views.resend_verification_view, name='resend-verification'),
    path('auth/me/',                   views.me_view,                  name='me'),
    # ── Etapa 2 — Trial ──────────────────────────────────────────
    path('trial/status/',             trial_status_view,              name='trial-status'),
    path('plans/',                    plans_view,                     name='plans'),

        # Etapa 3 — Setup wizard
    path('setup/establishment/', setup_establishment_view, name='setup-establishment'),
    path('setup/status/',        setup_status_view,        name='setup-status'),
    path('setup/complete/',      setup_complete_view,      name='setup-complete'),
    path('team/',                        team_view,             name='team'),
    path('team/<int:member_id>/',        team_member_view,      name='team-member'),
    path('team/<int:member_id>/link-professional/', team_link_professional, name='team-link')
]


