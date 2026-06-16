# financial/models.py
import uuid
from django.utils import timezone
from django.db import models
from tenants.models import Tenant


class Product(models.Model):
    """
    Produto ou serviço extra vendável na comanda.
    Ex: Pomada Capilar, Shampoo, Gorjeta
    """
    class Category(models.TextChoices):
        PRODUCT = 'product', 'Produto'
        EXTRA   = 'extra',   'Serviço extra'
        OTHER   = 'other',   'Outro'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant       = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='products')
    name         = models.CharField(max_length=100)
    category     = models.CharField(max_length=20, choices=Category.choices, default=Category.PRODUCT)
    price        = models.DecimalField(max_digits=8, decimal_places=2)
    cost_price   = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                       help_text="Preço de custo — para cálculo de margem")
    stock_qty    = models.IntegerField(default=0, help_text="Quantidade em estoque")
    stock_alert  = models.IntegerField(default=5, help_text="Alerta quando estoque chegar aqui")
    track_stock  = models.BooleanField(default=True, help_text="False para gorjeta, desconto, etc.")
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'products'
        ordering     = ['category', 'name']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'

    def __str__(self):
        return f"{self.name} — R${self.price}"

    @property
    def stock_low(self):
        return self.track_stock and self.stock_qty <= self.stock_alert

    @property
    def margin_pct(self):
        if not self.price or float(self.price) == 0:
            return 0
        return round((1 - float(self.cost_price) / float(self.price)) * 100, 1)


class StockMovement(models.Model):
    """
    Movimentação de estoque.
    Criada automaticamente ao vender na comanda ou manualmente ao repor.
    """
    class Type(models.TextChoices):
        IN     = 'in',     'Entrada'
        OUT    = 'out',    'Saída'
        ADJUST = 'adjust', 'Ajuste'

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant     = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='stock_movements')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    type       = models.CharField(max_length=10, choices=Type.choices)
    quantity   = models.IntegerField(help_text="Positivo para entrada, negativo para saída")
    reason     = models.CharField(max_length=200, blank=True)
    cost_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
                                     help_text="Preço de custo nesta movimentação (se entrada)")
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} {'+' if self.quantity > 0 else ''}{self.quantity}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualiza stock_qty no produto
        self.product.stock_qty += self.quantity
        self.product.save(update_fields=['stock_qty', 'updated_at'])


class Comanda(models.Model):
    """
    Comanda vinculada a um agendamento.
    Criada automaticamente quando barbeiro clica em 'Iniciar atendimento'.
    """
    class Status(models.TextChoices):
        OPEN   = 'open',   'Aberta'
        CLOSED = 'closed', 'Fechada'

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant      = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='comandas')
    appointment = models.OneToOneField(
        'agenda.Appointment', on_delete=models.CASCADE, related_name='comanda'
    )
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    notes       = models.TextField(blank=True)
    opened_at   = models.DateTimeField(auto_now_add=True)
    closed_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table     = 'comandas'
        ordering     = ['-opened_at']
        verbose_name = 'Comanda'

    def __str__(self):
        return f"Comanda #{str(self.id)[:8]} — {self.appointment.client_name}"

    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def total_discount(self):
        return sum(item.discount_value for item in self.items.all())

    @property
    def total(self):
        return self.subtotal

    @property
    def total_commission(self):
        return sum(item.commission_value for item in self.items.filter(is_courtesy=False))


class CommandaItem(models.Model):
    """
    Item da comanda — serviço ou produto.
    O serviço do agendamento é criado automaticamente como primeiro item.
    """
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comanda        = models.ForeignKey(Comanda, on_delete=models.CASCADE, related_name='items')
    product        = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Null = serviço do agendamento"
    )
    description    = models.CharField(max_length=200, help_text="Nome do item na comanda")
    quantity       = models.PositiveIntegerField(default=1)
    unit_price     = models.DecimalField(max_digits=8, decimal_places=2)
    discount       = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                          help_text="Desconto por item em R$")
    is_courtesy    = models.BooleanField(default=False, help_text="Cortesia — não gera comissão")
    commission_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Copiado do profissional — editável por item"
    )
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comanda_items'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.description} x{self.quantity} — R${self.total}"

    @property
    def discount_value(self):
        return float(self.discount) * self.quantity

    @property
    def total(self):
        return round((float(self.unit_price) - float(self.discount)) * self.quantity, 2)

    @property
    def commission_value(self):
        if self.is_courtesy:
            return 0
        return round(self.total * float(self.commission_pct) / 100, 2)


class CashEntry(models.Model):
    """
    Entrada de caixa — gerada ao fechar comanda.
    """
    class PaymentMethod(models.TextChoices):
        PIX    = 'pix',    'Pix'
        CASH   = 'cash',   'Dinheiro'
        CREDIT = 'credit', 'Cartão de crédito'
        DEBIT  = 'debit',  'Cartão de débito'
        OTHER  = 'other',  'Outro'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant         = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cash_entries')
    appointment    = models.OneToOneField(
        'agenda.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cash_entry'
    )
    comanda        = models.OneToOneField(
        Comanda, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cash_entry'
    )
    professional   = models.ForeignKey(
        'agenda.Professional', on_delete=models.SET_NULL, null=True, blank=True
    )
    amount         = models.DecimalField(max_digits=8, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.PIX)
    description    = models.CharField(max_length=200, blank=True)
    is_manual      = models.BooleanField(default=False, help_text="Lançamento manual sem agendamento")
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cash_entries'
        ordering = ['-created_at']
        indexes  = [models.Index(fields=['tenant', 'created_at'])]

    def __str__(self):
        return f"R${self.amount} — {self.payment_method} — {self.created_at:%d/%m/%Y}"


class Expense(models.Model):
    """Despesa lançada manualmente pelo dono/gerente."""
 
    class Category(models.TextChoices):
        RENT        = 'rent',        'Aluguel'
        ENERGY      = 'energy',      'Energia elétrica'
        WATER       = 'water',       'Água'
        INTERNET    = 'internet',    'Internet'
        PRODUCT     = 'product',     'Compra de produto'
        SALARY      = 'salary',      'Salário fixo'
        COMMISSION  = 'commission',  'Comissão'
        MAINTENANCE = 'maintenance', 'Manutenção'
        MARKETING   = 'marketing',   'Marketing'
        OTHER       = 'other',       'Outros'
 
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='expenses')
    category    = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    description = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    date        = models.DateField(default=timezone.now)
    notes       = models.TextField(blank=True)
    created_by  = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-date', '-created_at']
 
    def __str__(self):
        return f"{self.get_category_display()} — R${self.amount} ({self.date})"
 
 
class AccountsPayable(models.Model):
    """Conta a pagar — recorrente ou única."""
 
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        PAID    = 'paid',    'Pago'
        OVERDUE = 'overdue', 'Em atraso'
 
    class Recurrence(models.TextChoices):
        ONCE    = 'once',    'Única'
        MONTHLY = 'monthly', 'Mensal'
        WEEKLY  = 'weekly',  'Semanal'
 
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant      = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='accounts_payable')
    description = models.CharField(max_length=200)
    category    = models.CharField(max_length=20, choices=Expense.Category.choices, default=Expense.Category.OTHER)
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    due_date    = models.DateField()
    recurrence  = models.CharField(max_length=10, choices=Recurrence.choices, default=Recurrence.ONCE)
    status      = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    notes       = models.TextField(blank=True)
    paid_at     = models.DateTimeField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_by  = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['due_date', '-created_at']
 
    @property
    def is_overdue(self):
        from datetime import date
        return self.status == 'pending' and self.due_date < date.today()
 
    def __str__(self):
        return f"{self.description} — R${self.amount} vence {self.due_date}"
    

class CommissionEntry(models.Model):
    """
    Registro individual de comissão por serviço realizado.
    Criado automaticamente no checkout da comanda.
    Só registra serviços — produtos não geram comissão.
    """
 
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant           = models.ForeignKey('tenants.Tenant',    on_delete=models.CASCADE, related_name='commission_entries')
    professional     = models.ForeignKey('agenda.Professional', on_delete=models.SET_NULL, null=True, related_name='commission_entries')
    appointment      = models.ForeignKey('agenda.Appointment',  on_delete=models.CASCADE, related_name='commission_entries')
 
    # Serviço realizado
    service_name     = models.CharField(max_length=200)
    service_price    = models.DecimalField(max_digits=10, decimal_places=2)
    commission_pct   = models.DecimalField(max_digits=5,  decimal_places=2)
    commission_amount= models.DecimalField(max_digits=10, decimal_places=2)
 
    # Pagamento
    payment_method   = models.CharField(max_length=20, default='pix')
 
    # Cliente
    client_name      = models.CharField(max_length=200, blank=True)
    client_phone     = models.CharField(max_length=30,  blank=True)
 
    # Data/hora do atendimento
    service_date     = models.DateField()
    service_time     = models.TimeField()
 
    # Controle
    is_paid          = models.BooleanField(default=False)
    paid_at          = models.DateTimeField(null=True, blank=True)
    payable          = models.ForeignKey(
        'financial.AccountsPayable',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='commission_entries',
    )
 
    created_at       = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-service_date', '-service_time']
        indexes  = [
            models.Index(fields=['tenant', 'professional', 'service_date']),
            models.Index(fields=['tenant', 'is_paid']),
        ]
 
    def __str__(self):
        return f"{self.professional} — {self.service_name} R${self.commission_amount} ({self.service_date})"
 
    @property
    def professional_name(self):
        return self.professional.name if self.professional else '—'