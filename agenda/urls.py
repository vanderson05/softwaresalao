# ════════════════════════════════════════════════════════════════
# agenda/urls.py — versão completa Etapa 3 + Etapa 4
# ════════════════════════════════════════════════════════════════
 
from django.urls import path
from . import views
from . import views_appointment
 
urlpatterns = [
    # ── Etapa 3 — Profissionais ───────────────────────────────
    path('professionals/',
         views.professionals_view,
         name='professionals'),
    path('professionals/<uuid:professional_id>/',
         views.professional_detail_view,
         name='professional-detail'),
    path('professionals/<uuid:professional_id>/schedules/',
         views.schedules_view,
         name='schedules'),
    path('professionals/<uuid:professional_id>/blocks/',
         views.schedule_blocks_view,
         name='schedule-blocks'),
 
    # ── Etapa 3 — Serviços ────────────────────────────────────
    path('services/',
         views.services_view,
         name='services'),
    path('services/<uuid:service_id>/',
         views.service_detail_view,
         name='service-detail'),
 
    # ── Etapa 3 — Horários ────────────────────────────────────
    path('schedules/bulk/',
         views.schedules_bulk_view,
         name='schedules-bulk'),
 
    # ── Etapa 3 — Slots ───────────────────────────────────────
    path('slots/',
         views.slots_view,
         name='slots'),
    path('slots/next/',
         views.next_slots_view,
         name='slots-next'),
 
    # ── Etapa 4 — Agendamentos ────────────────────────────────
    path('appointments/',
         views_appointment.appointments_view,
         name='appointments'),
    path('appointments/<uuid:appointment_id>/',
         views_appointment.appointment_detail_view,
         name='appointment-detail'),
    path('appointments/<uuid:appointment_id>/confirm/',
         views_appointment.appointment_confirm_view,
         name='appointment-confirm'),
    path('appointments/<uuid:appointment_id>/cancel/',
         views_appointment.appointment_cancel_view,
         name='appointment-cancel'),
    path('appointments/<uuid:appointment_id>/complete/',
         views_appointment.appointment_complete_view,
         name='appointment-complete'),
    path('appointments/<uuid:appointment_id>/no-show/',
         views_appointment.appointment_no_show_view,
         name='appointment-no-show'),
 
    # ── Etapa 4 — Agenda visual ───────────────────────────────
    path('agenda/day/',
         views_appointment.agenda_day_view,
         name='agenda-day'),
    path('agenda/week/',
         views_appointment.agenda_week_view,
         name='agenda-week'),
]