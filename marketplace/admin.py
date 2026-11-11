from django.contrib import admin
from .models import Business, Product

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'whatsapp', 'is_active') # Muestra estas columnas en la lista
    list_filter = ('is_active', 'business_type')                     # Agrega filtros laterales rápidos
    list_editable = ('is_active',)                                   # Permite cambiar el estado (activo/inactivo) directamente en la tabla

admin.site.register(Product)
