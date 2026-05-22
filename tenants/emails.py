

# ═══════════════════════════════════════════════════════════════
# apps/tenants/emails.py
# ═══════════════════════════════════════════════════════════════

from django.core.mail import send_mail
from django.conf import settings


def send_welcome_email(user, tenant, token):
    """
    E-mail de boas-vindas + link de verificação.
    Enviado logo após o cadastro.
    """
    verify_url = f"{settings.FRONTEND_URL}/verificar-email?token={token}"

    subject = f"Bem-vindo ao Beauti, {tenant.name}!"
    message = f"""
Olá!

Seu cadastro no Beauti foi realizado com sucesso.

Estabelecimento: {tenant.name}
E-mail de acesso: {user.email}
Plano: Trial gratuito por 14 dias

Para acessar o painel, confirme seu e-mail clicando no link abaixo:
{verify_url}

Este link expira em 24 horas.

Se você não realizou este cadastro, ignore este e-mail.

Equipe Beauti
    """.strip()

    send_mail(
        subject      = subject,
        message      = message,
        from_email   = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [user.email],
        fail_silently  = False,
    )


def send_resend_verification_email(user, token):
    """Reenvia o link de verificação de e-mail."""
    verify_url = f"{settings.FRONTEND_URL}/verificar-email?token={token}"

    subject = "Beauti — Novo link de verificação"
    message = f"""
Você solicitou um novo link de verificação de e-mail.

Clique no link abaixo para confirmar:
{verify_url}

Este link expira em 24 horas.

Equipe Beauti
    """.strip()

    send_mail(
        subject        = subject,
        message        = message,
        from_email     = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [user.email],
        fail_silently  = False,
    )


def send_trial_expiry_warning(tenant, days_remaining):
    """Aviso de expiração do trial."""
    subject = f"Beauti — Seu trial expira em {days_remaining} dia(s)"
    message = f"""
Olá, {tenant.name}!

Seu período de trial gratuito expira em {days_remaining} dia(s).

Para continuar usando o Beauti, escolha seu plano:
{settings.FRONTEND_URL}/planos

Planos disponíveis:
- Starter (1 profissional): R$99,90/mês
- Pro (2-5 profissionais): R$149,90/mês
- Advanced (6-15 profissionais): R$199,90/mês
- Enterprise (+15 profissionais): R$279,90/mês

Equipe Beauti
    """.strip()

    send_mail(
        subject        = subject,
        message        = message,
        from_email     = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [tenant.email],
        fail_silently  = True,
    )
