from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# ==========================================
# MODELO DE NEGOCIOS / TIENDAS
# ==========================================
class Business(models.Model):
    # Opciones disponibles para clasificar el modelo operativo del negocio
    BUSINESS_TYPE_CHOICES = [
        ('fisico', 'Local Físico / Tienda Establecida'),
        ('entrega', 'Entregas en Puntos / Puntos Medios'),
    ]

    # Relación uno a uno con el usuario de Django para el acceso exclusivo al panel
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Datos generales del comercio
    name = models.CharField(max_length=100) # Nombre del negocio
    description = models.TextField()        # Breve descripción de lo que venden u ofrecen
    whatsapp = models.CharField(max_length=20) # Número de contacto para pedidos por WhatsApp
    address = models.CharField(max_length=255) # Dirección física o referencia principal
    
    # Coordenadas geográficas para calcular la distancia y mostrarlos en el mapa interactivo
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Nuevos campos para diferenciar si es local establecido o entregas puntuales
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='fisico')
    delivery_zones = models.TextField(blank=True, null=True, help_text="Específica dónde entregas si no tienes local fijo")
    
    # 🕒 NUEVOS CAMPOS DE HORARIO DE ATENCIÓN
    opening_time = models.TimeField(null=True, blank=True, verbose_name="Hora de apertura")
    closing_time = models.TimeField(null=True, blank=True, verbose_name="Hora de cierre")

    # Indicador para desactivar el negocio sin borrarlo físicamente
    is_active = models.BooleanField(default=True, verbose_name="¿Empresa Activa?")

    def __str__(self):
        return self.name

    @property
    def is_open_now(self):
        """
        Calcula automáticamente si el negocio está abierto en este momento.
        Retorna: True (Abierto), False (Cerrado), o None (Si no configuró horario).
        """
        if not self.opening_time or not self.closing_time:
            return None

        now = timezone.localtime().time()

        # Caso 1: Horario normal en el mismo día (ej. 09:00 a 20:00)
        if self.opening_time <= self.closing_time:
            return self.opening_time <= now <= self.closing_time
        
        # Caso 2: Horario nocturno que cruza la medianoche (ej. 18:00 a 02:00)
        else:
            return now >= self.opening_time or now <= self.closing_time


# ==========================================
# MODELO DE PRODUCTOS
# ==========================================
class Product(models.Model):
    # Categorías completas (Estilo Mercado Libre + Comida)
    CATEGORY_CHOICES = [
        ('comida', 'Comida y Antojitos'),
        ('vehiculos', 'Vehículos'),
        ('supermercado', 'Supermercado'),
        ('tecnologia', 'Tecnología'),
        ('electrodomesticos', 'Electrodomésticos'),
        ('hogar', 'Hogar y Muebles'),
        ('moda', 'Moda'),
        ('deportes', 'Deportes y Fitness'),
        ('herramientas', 'Herramientas'),
        ('construccion', 'Construcción'),
        ('mascotas', 'Mascotas'),
        ('abarrotes', 'Abarrotes'),
        ('servicios', 'Servicios y Oficios'),
        ('otro', 'Otro'),
    ]

    # Condición de la pieza
    CONDITION_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('usado', 'De uso / Seminuevo'),
    ]

    # Relación de muchos a uno: Cada producto pertenece obligatoriamente a un negocio
    business = models.ForeignKey('Business', on_delete=models.CASCADE)
    
    # Información del producto
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Campo para guardar la condición (por defecto será Nuevo)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='nuevo')
    
    # 🛡️ Garantía del Producto
    warranty = models.CharField(max_length=255, blank=True, null=True, verbose_name="Garantía del producto", help_text="Ej. Sin garantía, 30 días con el vendedor, etc.")

    # Control de ofertas y promociones generales
    is_promo = models.BooleanField(default=False)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Control de Promociones Exprés (Ofertas Relámpago de 24 horas)
    is_express_promo = models.BooleanField(default=False)
    express_promo_start = models.DateTimeField(null=True, blank=True)
    express_promo_end = models.DateTimeField(null=True, blank=True)
    
    # Control de Destacado Semanal (Patrocinado / 7 días)
    is_featured = models.BooleanField(default=False, verbose_name="¿Producto Destacado?")
    featured_until = models.DateTimeField(null=True, blank=True, verbose_name="Destacado Hasta")

    # Archivo de imagen del producto y asignación de categoría
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    # Imágenes adicionales 2 y 3
    image_2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image_3 = models.ImageField(upload_to='products/', null=True, blank=True)
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='otro')

    # Control de stock / disponibilidad (Disponible / Agotado)
    is_available = models.BooleanField(default=True, verbose_name="Disponible en stock")

    def __str__(self):
        return self.name

    @property
    def is_express_active(self):
        """Verifica automáticamente si la promoción exprés sigue vigente dentro de las 24 horas."""
        if self.is_express_promo and self.express_promo_end:
            return timezone.now() <= self.express_promo_end
        return False

    def activate_express_promo(self, hours=24):
        """Activa la promoción exprés estableciendo una vigencia exacta de 24 horas."""
        self.is_express_promo = True
        self.express_promo_start = timezone.now()
        self.express_promo_end = timezone.now() + timedelta(hours=hours)
        self.save()

    @property
    def is_featured_active(self):
        """Verifica automáticamente si la suscripción de destacado por 7 días sigue vigente."""
        if self.is_featured and self.featured_until:
            return timezone.now() <= self.featured_until
        return False

    def activate_featured_promo(self, days=7):
        """Activa la suscripción destacada por una semana (7 días)."""
        self.is_featured = True
        self.featured_until = timezone.now() + timedelta(days=days)
        self.save()

    @property
    def discount_percentage(self):
        """Calcula automáticamente el porcentaje de descuento cuando hay un precio de oferta."""
        if self.promo_price and self.price and self.price > 0 and self.promo_price < self.price:
            discount = ((self.price - self.promo_price) / self.price) * 100
            return round(discount)
        return 0
    
# ==========================================
# MODELO DE RESEÑAS Y VALORACIONES
# ==========================================
class Review(models.Model):
    # Relación con el producto evaluado
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    
    # Datos de la opinión del cliente
    author_name = models.CharField(max_length=50, default="Vecino Anónimo")
    rating = models.IntegerField(choices=[(i, f"{i} Estrellas") for i in range(1, 6)], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True) # Fecha y hora de creación automática

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐ por {self.author_name}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Evita duplicados

    def __str__(self):
        return f"{self.user.username} -> {self.product.name}"
