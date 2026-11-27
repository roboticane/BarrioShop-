from django.contrib import admin
from .models import Business, Product, PromoBanner


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'whatsapp', 'is_active')  # Muestra estas columnas en la lista
    list_filter = ('is_active', 'business_type')                      # Agrega filtros laterales rápidos
    list_editable = ('is_active',)                                    # Permite cambiar el estado (activo/inactivo) directamente en la tabla
    search_fields = ('name', 'whatsapp', 'address')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'category', 'price', 'promo_price', 'is_available', 'is_featured')
    list_filter = ('is_available', 'is_featured', 'category', 'condition')
    list_editable = ('is_available', 'is_featured')
    search_fields = ('name', 'description', 'search_tags', 'business__name')


@admin.register(PromoBanner)
class PromoBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'bg_style', 'order', 'is_active', 'start_date', 'end_date')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'bg_style')
    search_fields = ('title', 'subtitle', 'badge_text')
