# ════════════════════════════════════════════════════════════════
# financial/admin.py
# ════════════════════════════════════════════════════════════════
 
from django.contrib import admin
from .models import Product, StockMovement, Comanda, CommandaItem, CashEntry
 
 
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'tenant', 'category', 'price', 'stock_qty', 'stock_low', 'is_active']
    list_filter   = ['category', 'is_active', 'tenant']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']
 
 
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display  = ['product', 'type', 'quantity', 'reason', 'created_at']
    list_filter   = ['type']
    readonly_fields = ['id', 'created_at']
 
 
@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display  = ['appointment', 'tenant', 'status', 'opened_at', 'closed_at']
    list_filter   = ['status', 'tenant']
    readonly_fields = ['id', 'opened_at', 'closed_at']
 
 
@admin.register(CommandaItem)
class CommandaItemAdmin(admin.ModelAdmin):
    list_display  = ['description', 'quantity', 'unit_price', 'discount', 'is_courtesy', 'commission_pct']
    list_filter   = ['is_courtesy']
    readonly_fields = ['id', 'created_at']
 
 
@admin.register(CashEntry)
class CashEntryAdmin(admin.ModelAdmin):
    list_display  = ['amount', 'commission_amount', 'payment_method', 'professional', 'tenant', 'created_at']
    list_filter   = ['payment_method', 'tenant']
    readonly_fields = ['id', 'created_at']
 