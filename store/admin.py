from django.contrib import admin
from .models import Order, OrderItem, Product, Category


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    # ✅ ADD paid HERE
    list_display = ('id', 'user', 'status', 'paid', 'created_at')
    list_filter = ('status', 'paid')
    list_editable = ('status', 'paid')
    inlines = [OrderItemInline]


admin.site.register(Order, OrderAdmin)
admin.site.register(Product)
admin.site.register(Category)
