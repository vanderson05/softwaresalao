# ════════════════════════════════════════════════════════════════
# clients/urls.py
# ════════════════════════════════════════════════════════════════
 
from django.urls import path
from .views_crm import (
    clients_list_view,
    client_detail_view,
    insight_summary_view,
    insight_inactive_view,
    insight_birthdays_view,
    insight_top_clients_view,
    insight_new_clients_view,
    subscriptions_view,
    subscription_detail_view,
    subscription_renew_view,
)
 
urlpatterns = [
    # Clientes
    path('crm/clients/',             clients_list_view,          name='crm-clients'),
    path('crm/clients/<uuid:client_id>/', client_detail_view,    name='crm-client-detail'),
 
    # Insights
    path('crm/insights/summary/',    insight_summary_view,       name='crm-summary'),
    path('crm/insights/inactive/',   insight_inactive_view,      name='crm-inactive'),
    path('crm/insights/birthdays/',  insight_birthdays_view,     name='crm-birthdays'),
    path('crm/insights/top/',        insight_top_clients_view,   name='crm-top'),
    path('crm/insights/new/',        insight_new_clients_view,   name='crm-new'),
 
    # Assinaturas
    path('crm/subscriptions/',       subscriptions_view,         name='crm-subscriptions'),
    path('crm/subscriptions/<uuid:subscription_id>/',
         subscription_detail_view,   name='crm-subscription-detail'),
    path('crm/subscriptions/<uuid:subscription_id>/renew/',
         subscription_renew_view,    name='crm-subscription-renew'),
]