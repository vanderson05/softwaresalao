from django.urls import path
from . import views
 
urlpatterns = [
    # Profissionais
    path('professionals/',                     views.professionals_view,        name='professionals'),
    path('professionals/<uuid:professional_id>/', views.professional_detail_view, name='professional-detail'),
 
    # Serviços
    path('services/',                views.services_view,        name='services'),
    path('services/<uuid:service_id>/', views.service_detail_view, name='service-detail'),
 
    # Horários
    path('professionals/<uuid:professional_id>/schedules/', views.schedules_view,        name='schedules'),
    path('professionals/<uuid:professional_id>/blocks/',    views.schedule_blocks_view,  name='schedule-blocks'),
    path('schedules/bulk/',                                 views.schedules_bulk_view,   name='schedules-bulk'),
 
    # Slots disponíveis
    path('slots/',      views.slots_view,      name='slots'),
    path('slots/next/', views.next_slots_view, name='slots-next'),
]