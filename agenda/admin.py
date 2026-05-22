# ════════════════════════════════════════════════════════════════
# agenda/admin.py
# ════════════════════════════════════════════════════════════════

from django.contrib import admin
from .models import Professional, Service, Schedule, ScheduleBlock, Appointment


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display  = ['name', 'tenant', 'slot_interval', 'commission_pct', 'is_active']
    list_filter   = ['is_active', 'slot_interval', 'tenant']
    search_fields = ['name', 'tenant__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ['name', 'tenant', 'duration_min', 'price', 'is_active']
    list_filter   = ['is_active', 'tenant']
    search_fields = ['name', 'tenant__name']
    filter_horizontal = ['professionals']
    readonly_fields = ['id', 'created_at']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display  = ['professional', 'weekday', 'start_time', 'end_time', 'is_active']
    list_filter   = ['weekday', 'is_active']
    search_fields = ['professional__name', 'professional__tenant__name']


@admin.register(ScheduleBlock)
class ScheduleBlockAdmin(admin.ModelAdmin):
    list_display  = ['professional', 'date', 'start_time', 'end_time', 'reason']
    list_filter   = ['date']
    search_fields = ['professional__name']
    readonly_fields = ['id', 'created_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ['client_name', 'service', 'professional', 'starts_at', 'status', 'source']
    list_filter   = ['status', 'source', 'tenant']
    search_fields = ['client_name', 'client_phone']
    readonly_fields = ['id', 'created_at', 'updated_at']


# ════════════════════════════════════════════════════════════════
# INSTRUÇÕES COMPLETAS — ETAPA 3
# ════════════════════════════════════════════════════════════════
"""
ARQUIVOS GERADOS E ONDE COLOCAR:
═══════════════════════════════════════════════════════════════
┌──────────────────────────────────┬──────────────────────────────────┬──────────┐
│ Arquivo gerado                   │ Destino                          │ Ação     │
├──────────────────────────────────┼──────────────────────────────────┼──────────┤
│ agenda_models.py                 │ agenda/models.py                 │ CRIAR    │
│ agenda_slots.py                  │ agenda/slots.py                  │ CRIAR    │
│ agenda_serializers.py            │ agenda/serializers.py            │ CRIAR    │
│ agenda_views.py                  │ agenda/views.py                  │ CRIAR    │
│ views_setup_e_urls.py (parte 1)  │ tenants/views_setup.py           │ CRIAR    │
│ views_setup_e_urls.py (parte 2)  │ agenda/urls.py                   │ CRIAR    │
│ views_setup_e_urls.py (parte 3)  │ tenants/urls.py                  │ SUBSTITUIR│
│ admin.py (início deste arquivo)  │ agenda/admin.py                  │ CRIAR    │
└──────────────────────────────────┴──────────────────────────────────┴──────────┘

NOTA: views_setup_e_urls.py tem 3 seções separadas por comentários
      com aspas triplas — cada seção vai para um arquivo diferente.


TAMBÉM PRECISA CRIAR:
═══════════════════════════════════════════════════════════════
agenda/urls.py  ← copiar o conteúdo dentro das aspas triplas
tenants/urls.py ← copiar o conteúdo dentro das aspas triplas (versão completa)


softwaresalao/urls.py — ADICIONAR linha do agenda:
═══════════════════════════════════════════════════════════════
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tenants.urls')),
    path('api/', include('agenda.urls')),   ← ADICIONAR
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]


CLIENTS APP — criar models.py mínimo para não quebrar FK do Appointment:
═══════════════════════════════════════════════════════════════
# clients/models.py
import uuid
from django.db import models
from tenants.models import Tenant

class Client(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='clients')
    name       = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'clients'
        unique_together = ('tenant', 'phone')

    def __str__(self):
        return f"{self.name} ({self.phone})"


COMANDOS:
═══════════════════════════════════════════════════════════════
python manage.py makemigrations agenda clients
python manage.py migrate
python manage.py runserver


RODAR TESTES:
═══════════════════════════════════════════════════════════════
python test_api.py   ← 51 testes anteriores devem continuar passando


TESTAR ETAPA 3 MANUALMENTE (com token do login):
═══════════════════════════════════════════════════════════════

# 1. Status do wizard (deve mostrar tudo False)
GET /api/setup/status/

# 2. Passo 1 — dados do estabelecimento
PATCH /api/setup/establishment/
{
  "address": "Av. Cillo, 320",
  "city": "Americana",
  "business_hours": [
    {"weekday": 0, "open_time": "13:00", "close_time": "18:00"},
    {"weekday": 1, "open_time": "09:00", "close_time": "18:00"},
    {"weekday": 2, "open_time": "09:00", "close_time": "18:00"},
    {"weekday": 3, "open_time": "09:00", "close_time": "18:00"},
    {"weekday": 4, "open_time": "09:00", "close_time": "18:00"},
    {"weekday": 5, "open_time": "09:00", "close_time": "13:00"},
    {"weekday": 6, "is_closed": true}
  ]
}

# 3. Passo 2 — profissional
POST /api/professionals/
{"name": "Carlão", "commission_pct": 40, "slot_interval": 30}

# 4. Passo 3 — serviços
POST /api/services/
{"name": "Corte masculino", "duration_min": 30, "price": 35.00}

POST /api/services/
{"name": "Corte + Barba", "duration_min": 50, "price": 55.00}

# 5. Passo 4 — horários do profissional
POST /api/schedules/bulk/
{
  "professional_id": "UUID_DO_CARLAO",
  "schedules": [
    {"weekday": 0, "start_time": "13:00", "end_time": "18:00"},
    {"weekday": 1, "start_time": "09:00", "end_time": "18:00"},
    {"weekday": 2, "start_time": "09:00", "end_time": "18:00"},
    {"weekday": 3, "start_time": "09:00", "end_time": "18:00"},
    {"weekday": 4, "start_time": "09:00", "end_time": "18:00"},
    {"weekday": 5, "start_time": "09:00", "end_time": "13:00"}
  ]
}

# 6. Concluir wizard
POST /api/setup/complete/

# 7. Testar slots
GET /api/slots/?service_id=UUID&date=2026-05-25

# 8. Próximos slots disponíveis
GET /api/slots/next/?service_id=UUID&days=7
"""