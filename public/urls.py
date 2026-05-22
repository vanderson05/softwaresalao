from django.urls import path
from . import views
 
urlpatterns = [
    # Home — lista barbearias
    path('b/',                                          views.home_view,                    name='public-home'),
 
    # Perfil público — sem auth
    path('b/<slug:slug>/',                              views.profile_view,                 name='public-profile'),
    path('b/<slug:slug>/services/',                     views.public_services_view,         name='public-services'),
    path('b/<slug:slug>/professionals/',                views.public_professionals_view,    name='public-professionals'),
    path('b/<slug:slug>/packages/',                     views.public_packages_view,         name='public-packages'),
 
    # Auth cliente final
    path('b/<slug:slug>/auth/request-code/',            views.auth_request_code_view,       name='client-request-code'),
    path('b/<slug:slug>/auth/verify-code/',             views.auth_verify_code_view,        name='client-verify-code'),
 
    # Área logada do cliente
    path('b/<slug:slug>/me/',                           views.client_me_view,               name='client-me'),
    path('b/<slug:slug>/slots/',                        views.public_slots_view,            name='public-slots'),
    path('b/<slug:slug>/book/',                         views.book_view,                    name='public-book'),
    path('b/<slug:slug>/my-appointments/',              views.my_appointments_view,         name='my-appointments'),
    path('b/<slug:slug>/my-appointments/<uuid:appointment_id>/cancel/',
         views.my_appointment_cancel_view,
         name='my-appointment-cancel'),
]