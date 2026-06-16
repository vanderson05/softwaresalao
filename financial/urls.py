# ════════════════════════════════════════════════════════════════
# financial/urls.py
# ════════════════════════════════════════════════════════════════
 
from django.urls import path
from . import views
from financial.views_expenses import (
    expenses_view,
    expense_detail_view,
    payables_view,
    payable_detail_view,
    financial_overview_view,
)

from financial.views_commission import (
    commission_payables_view,
    commission_entries_view,
    generate_commission_payables_view,
    pay_commission_payable_view,
)

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

    path('financial/expenses/',           expenses_view,          name='expenses'),
    path('financial/expenses/<uuid:expense_id>/', expense_detail_view, name='expense-detail'),
    path('financial/payables/',           payables_view,          name='payables'),
    path('financial/payables/<uuid:payable_id>/', payable_detail_view, name='payable-detail'),
    path('financial/overview/',           financial_overview_view, name='financial-overview'),

    path('financial/commission-payables/',
        commission_payables_view, name='commission-payables'),
    
    path('financial/commission-payables/generate/',
        generate_commission_payables_view, name='commission-generate'),
    
    path('financial/commission-payables/<uuid:payable_id>/pay/',
        pay_commission_payable_view, name='commission-pay'),
    
    path('financial/commission-entries/',
        commission_entries_view, name='commission-entries'),
]
 