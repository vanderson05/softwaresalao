# tenants/views_team.py
# Gestão completa de equipe — membros, acessos e profissionais

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from tenants.models import Tenant, TenantUser
from tenants.permissions import TenantAccessPermission
from agenda.models import Professional


def _serialize_member(tu: TenantUser) -> dict:
    """Serializa um membro da equipe."""
    professional = None
    try:
        prof = tu.user.professional_profile
        if prof.tenant == tu.tenant:
            professional = {
                'id':   str(prof.id),
                'name': prof.name,
            }
    except Exception:
        pass

    return {
        'id':           tu.id,
        'user_id':      tu.user.id,
        'name':         f"{tu.user.first_name} {tu.user.last_name}".strip() or tu.user.username,
        'email':        tu.user.email,
        'role':         tu.role,
        'title':        getattr(tu, 'title', '') or '',
        'is_active':    tu.user.is_active,
        'professional': professional,
        'joined_at':    tu.created_at.isoformat() if hasattr(tu, 'created_at') else None,
    }


# ── Lista e cria membros ──────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([TenantAccessPermission])
def team_view(request):
    """
    GET  /api/team/  → lista todos os membros com acesso
    POST /api/team/  → cria novo membro
    """
    tenant = request.tenant

    if request.method == 'GET':
        members = TenantUser.objects.filter(
            tenant=tenant
        ).select_related('user').order_by('user__first_name')

        return Response([_serialize_member(m) for m in members])

    # POST — cria membro
    if request.tenant_role != 'owner':
        return Response({'error': 'Apenas o dono pode criar acessos.'}, status=403)

    # Validações
    name     = request.data.get('name', '').strip()
    email    = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '').strip()
    role     = request.data.get('role', 'professional')
    title    = request.data.get('title', '').strip()

    if not name or not email or not password:
        return Response({'error': 'Nome, e-mail e senha são obrigatórios.'}, status=400)

    if len(password) < 6:
        return Response({'error': 'Senha deve ter pelo menos 6 caracteres.'}, status=400)

    valid_roles = ['manager', 'receptionist', 'professional']
    if role not in valid_roles:
        return Response({'error': f'Role inválida. Use: {", ".join(valid_roles)}'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Este e-mail já está cadastrado.'}, status=400)

    # Verifica limite de profissionais do plano
    if role == 'professional':
        PLAN_MAX_PROFESSIONALS = {
            'trial':      999,
            'starter':    1,
            'pro':        5,
            'advanced':   15,
            'enterprise': 999,
        }
        max_profs = PLAN_MAX_PROFESSIONALS.get(tenant.plan, 1)
        current   = TenantUser.objects.filter(tenant=tenant, role='professional').count()
        if current >= max_profs:
            return Response({
                'error': f'Limite de {max_profs} profissional(is) para o plano {tenant.plan}.'
            }, status=400)

    # Cria professional vinculado se role = professional
    professional_id = request.data.get('professional_id')

    with transaction.atomic():
        # Cria usuário
        names    = name.split(' ', 1)


        user = User.objects.create_user(
            username   = email,
            email      = email,
            password   = password,
            first_name = names[0],
            last_name  = names[1] if len(names) > 1 else '',
        )

        # Cria TenantUser
        tenant_user = TenantUser.objects.create(
            user   = user,
            tenant = tenant,
            role   = role,
            title  = title,
        )

        # Vincula ao Professional existente se informado
        if professional_id and role == 'professional':
            try:
                prof = Professional.objects.get(id=professional_id, tenant=tenant)
                if not prof.user:
                    prof.user = user
                    prof.save(update_fields=['user'])
            except Professional.DoesNotExist:
                pass

    return Response({
        'message': f'Acesso criado para {name}.',
        'member':  _serialize_member(tenant_user),
    }, status=201)


# ── Detalhe, edição e remoção ─────────────────────────────────

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([TenantAccessPermission])
def team_member_view(request, member_id):
    """
    GET    /api/team/{id}/  → detalhe do membro
    PATCH  /api/team/{id}/  → atualiza role, title, senha
    DELETE /api/team/{id}/  → remove acesso
    """
    tenant = request.tenant

    try:
        member = TenantUser.objects.select_related('user').get(
            id=member_id, tenant=tenant
        )
    except TenantUser.DoesNotExist:
        return Response({'error': 'Membro não encontrado.'}, status=404)

    # Não pode mexer no próprio owner
    if member.role == 'owner' and request.tenant_role != 'owner':
        return Response({'error': 'Sem permissão.'}, status=403)

    if request.method == 'GET':
        return Response(_serialize_member(member))

    if request.tenant_role != 'owner':
        return Response({'error': 'Apenas o dono pode alterar acessos.'}, status=403)

    # Não pode alterar o próprio owner via API
    if member.role == 'owner':
        return Response({'error': 'Não é possível alterar o dono via API.'}, status=400)

    if request.method == 'PATCH':
        user = member.user

        if 'title' in request.data:
            member.title = request.data['title']

        if 'role' in request.data:
            new_role = request.data['role']
            if new_role not in ['manager', 'receptionist', 'professional']:
                return Response({'error': 'Role inválida.'}, status=400)
            member.role = new_role

        if 'name' in request.data:
            names = request.data['name'].strip().split(' ', 1)
            user.first_name = names[0]
            user.last_name  = names[1] if len(names) > 1 else ''
            user.save(update_fields=['first_name', 'last_name'])

        if 'new_password' in request.data:
            pwd = request.data['new_password']
            if len(pwd) < 6:
                return Response({'error': 'Senha deve ter pelo menos 6 caracteres.'}, status=400)
            user.set_password(pwd)
            user.save()

        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
            user.save(update_fields=['is_active'])

        member.save()
        return Response({
            'message': 'Membro atualizado.',
            'member':  _serialize_member(member),
        })

    if request.method == 'DELETE':
        user = member.user
        with transaction.atomic():
            # Desvincula professional se houver
            try:
                prof = user.professional_profile
                if prof.tenant == tenant:
                    prof.user = None
                    prof.save(update_fields=['user'])
            except Exception:
                pass

            member.delete()
            user.is_active = False
            user.save(update_fields=['is_active'])

        return Response({'message': f'Acesso de {user.first_name} removido.'})


# ── Vincular membro a profissional ────────────────────────────

@api_view(['POST'])
@permission_classes([TenantAccessPermission])
def team_link_professional(request, member_id):
    """
    POST /api/team/{id}/link-professional/
    Vincula um membro (role=professional) a um Professional da agenda.
    Body: {"professional_id": "uuid"}
    """
    tenant = request.tenant

    if request.tenant_role != 'owner':
        return Response({'error': 'Sem permissão.'}, status=403)

    try:
        member = TenantUser.objects.select_related('user').get(
            id=member_id, tenant=tenant
        )
    except TenantUser.DoesNotExist:
        return Response({'error': 'Membro não encontrado.'}, status=404)

    if member.role != 'professional':
        return Response({'error': 'Apenas membros com role professional podem ser vinculados.'}, status=400)

    professional_id = request.data.get('professional_id')
    if not professional_id:
        return Response({'error': 'professional_id obrigatório.'}, status=400)

    try:
        prof = Professional.objects.get(id=professional_id, tenant=tenant)
    except Professional.DoesNotExist:
        return Response({'error': 'Profissional não encontrado.'}, status=404)

    if prof.user and prof.user != member.user:
        return Response({'error': 'Este profissional já tem outro usuário vinculado.'}, status=400)

    prof.user = member.user
    prof.save(update_fields=['user'])

    return Response({
        'message': f'{member.user.first_name} vinculado a {prof.name}.',
        'professional': {'id': str(prof.id), 'name': prof.name},
    })