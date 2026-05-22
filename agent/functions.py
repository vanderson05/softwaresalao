# agent/functions.py
# Definições das 4 funções para GPT function calling
# + executores que chamam a API Django internamente

import json
from django.utils import timezone


# ── Definições para a OpenAI API ─────────────────────────────────────────────

FUNCTION_DEFINITIONS = [
    {
        "name": "get_services",
        "description": (
            "Lista todos os serviços disponíveis da barbearia com nome, preço e duração. "
            "Use quando o cliente perguntar o que a barbearia oferece ou quais serviços existem."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_available_slots",
        "description": (
            "Retorna os próximos horários disponíveis para um serviço específico. "
            "Use SEMPRE que o cliente quiser saber horários disponíveis ou agendar. "
            "Nunca invente horários — sempre chame esta função."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service_id": {
                    "type":        "string",
                    "description": "ID do serviço desejado pelo cliente (UUID).",
                },
                "days": {
                    "type":        "integer",
                    "description": "Quantos dias à frente verificar. Default: 7.",
                    "default":     7,
                },
                "professional_id": {
                    "type":        "string",
                    "description": "ID do profissional preferido (opcional). Se não informado, busca em todos.",
                },
            },
            "required": ["service_id"],
        },
    },
    {
        "name": "create_appointment",
        "description": (
            "Cria um agendamento no sistema. Use SOMENTE após confirmar com o cliente: "
            "serviço, profissional, data/hora, nome e telefone. "
            "Nunca confirme agendamento sem chamar esta função."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "professional_id": {
                    "type":        "string",
                    "description": "ID do profissional (UUID).",
                },
                "service_id": {
                    "type":        "string",
                    "description": "ID do serviço (UUID).",
                },
                "starts_at": {
                    "type":        "string",
                    "description": "Data e hora do agendamento no formato ISO 8601. Ex: 2026-05-26T09:00:00",
                },
                "client_name": {
                    "type":        "string",
                    "description": "Nome completo do cliente.",
                },
                "client_phone": {
                    "type":        "string",
                    "description": "Telefone WhatsApp do cliente com DDD. Ex: 19999998888",
                },
            },
            "required": ["professional_id", "service_id", "starts_at", "client_name", "client_phone"],
        },
    },
    {
        "name": "cancel_appointment",
        "description": (
            "Cancela o próximo agendamento futuro do cliente pelo telefone. "
            "Use quando o cliente pedir para cancelar ou remarcar."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "client_phone": {
                    "type":        "string",
                    "description": "Telefone WhatsApp do cliente com DDD.",
                },
                "reason": {
                    "type":        "string",
                    "description": "Motivo do cancelamento (opcional).",
                },
            },
            "required": ["client_phone"],
        },
    },
]


# ── Executores — chamam a API Django internamente ─────────────────────────────

def execute_function(name: str, arguments: dict, tenant) -> str:
    """
    Executa a função chamada pelo GPT e retorna resultado como string.
    Chamado pelo engine quando GPT retorna um tool_call.
    """
    try:
        if name == "get_services":
            return _get_services(tenant)
        elif name == "get_available_slots":
            return _get_available_slots(tenant, arguments)
        elif name == "create_appointment":
            return _create_appointment(tenant, arguments)
        elif name == "cancel_appointment":
            return _cancel_appointment(tenant, arguments)
        else:
            return json.dumps({"error": f"Função '{name}' não reconhecida."})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _get_services(tenant) -> str:
    from agenda.models import Service
    services = Service.objects.filter(tenant=tenant, is_active=True)
    result   = [
        {
            "id":           str(s.id),
            "name":         s.name,
            "price":        float(s.price),
            "duration_min": s.duration_min,
            "description":  s.description,
        }
        for s in services
    ]
    return json.dumps({
        "services": result,
        "total":    len(result),
    }, ensure_ascii=False)


def _get_available_slots(tenant, args: dict) -> str:
    from agenda.models import Service
    from agenda.slots import get_next_available_slots, get_available_slots
    from datetime import date, timedelta

    service_id      = args.get("service_id")
    days            = int(args.get("days", 7))
    professional_id = args.get("professional_id")

    try:
        service = Service.objects.get(id=service_id, tenant=tenant, is_active=True)
    except Service.DoesNotExist:
        return json.dumps({"error": "Serviço não encontrado."})

    if professional_id:
        from agenda.models import Professional
        try:
            professional = Professional.objects.get(
                id=professional_id, tenant=tenant, is_active=True
            )
            today  = timezone.localdate()
            result = []
            for i in range(days):
                d     = today + timedelta(days=i)
                slots = get_available_slots(professional, service, d)
                for slot in slots[:4]:
                    result.append({
                        "professional": {"id": str(professional.id), "name": professional.name},
                        "date":     d.isoformat(),
                        "time":     slot["time"],
                        "datetime": slot["datetime"],
                    })
        except Professional.DoesNotExist:
            return json.dumps({"error": "Profissional não encontrado."})
    else:
        result = get_next_available_slots(tenant, service, days_ahead=days)

    if not result:
        return json.dumps({
            "slots":   [],
            "message": "Nenhum horário disponível nos próximos dias. Tente outro serviço ou período.",
        }, ensure_ascii=False)

    return json.dumps({
        "service": {"id": str(service.id), "name": service.name},
        "slots":   result[:15],
        "total":   len(result),
    }, ensure_ascii=False)


def _create_appointment(tenant, args: dict) -> str:
    from django.test import RequestFactory
    from agenda.serializers_appointment import AppointmentCreateSerializer

    # Cria request fake para injetar tenant
    class FakeRequest:
        def __init__(self, tenant):
            self.tenant      = tenant
            self.tenant_role = 'owner'

    fake_request = FakeRequest(tenant)

    data = {
        "professional_id": args.get("professional_id"),
        "service_id":      args.get("service_id"),
        "starts_at":       args.get("starts_at"),
        "client_name":     args.get("client_name"),
        "client_phone":    args.get("client_phone", ""),
        "source":          "whatsapp",
    }

    serializer = AppointmentCreateSerializer(
        data=data,
        context={"request": fake_request}
    )

    if not serializer.is_valid():
        errors = []
        for field, msgs in serializer.errors.items():
            errors.append(f"{field}: {', '.join(msgs)}")
        return json.dumps({
            "success": False,
            "error":   " | ".join(errors),
        }, ensure_ascii=False)

    appointment = serializer.save()

    return json.dumps({
        "success":        True,
        "appointment_id": str(appointment.id),
        "status":         appointment.status,
        "client":         appointment.client_name,
        "service":        appointment.service.name,
        "professional":   appointment.professional.name,
        "starts_at":      appointment.starts_at.isoformat(),
        "ends_at":        appointment.ends_at.isoformat(),
        "price":          float(appointment.price_snapshot or 0),
        "address":        f"{tenant.address}, {tenant.city}",
    }, ensure_ascii=False)


def _cancel_appointment(tenant, args: dict) -> str:
    from agenda.models import Appointment
    from django.utils import timezone

    client_phone = args.get("client_phone", "").strip()
    reason       = args.get("reason", "Cancelado pelo cliente via WhatsApp")

    if not client_phone:
        return json.dumps({"success": False, "error": "Telefone não informado."})

    # Busca próximo agendamento futuro do cliente
    appointment = Appointment.objects.filter(
        tenant       = tenant,
        client_phone = client_phone,
        starts_at__gt = timezone.now(),
        status__in   = ['pending', 'confirmed'],
    ).order_by('starts_at').first()

    if not appointment:
        return json.dumps({
            "success": False,
            "message": "Nenhum agendamento futuro encontrado para este telefone.",
        }, ensure_ascii=False)

    appointment.status = Appointment.Status.CANCELLED
    appointment.notes  = f"{appointment.notes}\n[Cancelamento via WhatsApp] {reason}".strip()
    appointment.save(update_fields=['status', 'notes', 'updated_at'])

    return json.dumps({
        "success":      True,
        "cancelled":    str(appointment.id),
        "service":      appointment.service.name,
        "professional": appointment.professional.name,
        "was_at":       appointment.starts_at.isoformat(),
        "message":      "Agendamento cancelado com sucesso.",
    }, ensure_ascii=False)