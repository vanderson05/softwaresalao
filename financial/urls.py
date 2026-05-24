# ════════════════════════════════════════════════════════════════
# financial/urls.py
# ════════════════════════════════════════════════════════════════
 
from django.urls import path
from . import views
 
urlpatterns = [
    # Produtos e estoque
    path('financial/products/',                          views.products_view,          name='products'),
    path('financial/products/<uuid:product_id>/',        views.product_detail_view,    name='product-detail'),
    path('financial/products/<uuid:product_id>/stock/',  views.stock_movement_view,    name='stock-movement'),
    path('financial/stock/alerts/',                      views.stock_alerts_view,      name='stock-alerts'),
 
    # Comanda
    path('financial/appointments/<uuid:appointment_id>/comanda/',  views.comanda_view,          name='comanda'),
    path('financial/appointments/<uuid:appointment_id>/checkout/', views.comanda_checkout_view, name='checkout'),
    path('financial/comanda/items/<uuid:item_id>/',                views.comanda_item_view,     name='comanda-item'),
 
    # Caixa e relatórios
    path('financial/cashbox/',          views.cashbox_view,        name='cashbox'),
    path('financial/report/monthly/',   views.report_monthly_view, name='report-monthly'),
    path('financial/commissions/',      views.commissions_view,    name='commissions'),
]
 