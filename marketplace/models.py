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

    def __str__(self):
        return self.name  # Muestra el nombre del negocio en el panel de administración


# ==========================================
# MODELO DE PRODUCTOS
# ==========================================
class Product(models.Model):
    # Categorías completas (Estilo Mercado Libre + Comida + las que ya tenías)
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

    # ¡NUEVO! Condición de la pieza
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
    
    # ¡NUEVO! Campo para guardar la condición (por defecto será Nuevo)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='nuevo')
    
    # Control de ofertas y promociones generales
    is_promo = models.BooleanField(default=False)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Control de Promociones Exprés (Ofertas Relámpago de 24 horas)
    is_express_promo = models.BooleanField(default=False)
    express_promo_start = models.DateTimeField(null=True, blank=True)
    express_promo_end = models.DateTimeField(null=True, blank=True)
    
    # Archivo de imagen del producto y asignación de categoría
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    
    # ¡NUEVO! Imágenes adicionales 2 y 3
    image_2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image_3 = models.ImageField(upload_to='products/', null=True, blank=True)
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='otro')

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
