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
    
    # Campos para diferenciar si es local establecido o entregas puntuales
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='fisico')
    delivery_zones = models.TextField(blank=True, null=True, help_text="Específica dónde entregas si no tienes local fijo")
    
    # 📅 DÍAS LABORALES (Texto descriptivo general)
    work_days = models.CharField(max_length=150, default="Lunes a Sábado", blank=True, null=True, verbose_name="Días de labor / Atención")

    # 🕒 HORARIO DE LUNES A VIERNES
    opening_time = models.TimeField(null=True, blank=True, verbose_name="Apertura (Lun - Vie)")
    closing_time = models.TimeField(null=True, blank=True, verbose_name="Cierre (Lun - Vie)")

    # 🕒 HORARIO DE SÁBADO (Dejar vacío si no abren)
    saturday_opening_time = models.TimeField(null=True, blank=True, verbose_name="Apertura (Sábado)")
    saturday_closing_time = models.TimeField(null=True, blank=True, verbose_name="Cierre (Sábado)")

    # 🕒 HORARIO DE DOMINGO (Dejar vacío si descansan los domingos)
    sunday_opening_time = models.TimeField(null=True, blank=True, verbose_name="Apertura (Domingo)")
    sunday_closing_time = models.TimeField(null=True, blank=True, verbose_name="Cierre (Domingo)")

    # Indicador para desactivar el negocio sin borrarlo físicamente
    is_active = models.BooleanField(default=True, verbose_name="¿Empresa Activa?")

    def __str__(self):
        return self.name

    def get_today_schedule(self):
        """Retorna una tupla (apertura, cierre) correspondiente al día de la semana actual."""
        weekday = timezone.localtime().weekday() # 0=Lun, 1=Mar, 2=Mié, 3=Jue, 4=Vie, 5=Sáb, 6=Dom
        if weekday == 5:
            return (self.saturday_opening_time, self.saturday_closing_time)
        elif weekday == 6:
            return (self.sunday_opening_time, self.sunday_closing_time)
        else:
            return (self.opening_time, self.closing_time)

    @property
    def is_open_now(self):
        """
        Calcula automáticamente si el negocio está abierto según el día exacto de la semana.
        - Si hoy es Sábado/Domingo y dejaron vacíos esos campos, retorna False (Cerrado).
        - Si de Lun-Vie no configuraron horario, retorna None.
        """
        now = timezone.localtime()
        current_time = now.time()
        weekday = now.weekday()

        op_time, cl_time = self.get_today_schedule()

        # Si es fin de semana y no tiene horario configurado, está cerrado ese día
        if weekday in [5, 6] and (not op_time or not cl_time):
            # Solo marca cerrado si al menos tiene configurado horario entre semana
            if self.opening_time and self.closing_time:
                return False
            return None

        if not op_time or not cl_time:
            return None

        # Caso 1: Horario normal en el mismo día (ej. 10:00 a 13:00)
        if op_time <= cl_time:
            return op_time <= current_time <= cl_time
        
        # Caso 2: Horario nocturno que cruza la medianoche (ej. 18:00 a 02:00)
        else:
            return current_time >= op_time or current_time <= cl_time

    @property
    def today_hours_display(self):
        """Devuelve el texto del horario correspondiente al día de hoy."""
        op_time, cl_time = self.get_today_schedule()
        if op_time and cl_time:
            return f"{op_time.strftime('%H:%M')} - {cl_time.strftime('%H:%M')} hrs"
        return "Cerrado hoy"


# ==========================================
# MODELO DE PRODUCTOS
# ==========================================
class Product(models.Model):
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

    CONDITION_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('usado', 'De uso / Seminuevo'),
    ]

    business = models.ForeignKey('Business', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='nuevo')
    warranty = models.CharField(max_length=255, blank=True, null=True, verbose_name="Garantía del producto", help_text="Ej. Sin garantía, 30 días con el vendedor, etc.")

    is_promo = models.BooleanField(default=False)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_express_promo = models.BooleanField(default=False)
    express_promo_start = models.DateTimeField(null=True, blank=True)
    express_promo_end = models.DateTimeField(null=True, blank=True)
    
    is_featured = models.BooleanField(default=False, verbose_name="¿Producto Destacado?")
    featured_until = models.DateTimeField(null=True, blank=True, verbose_name="Destacado Hasta")

    image = models.ImageField(upload_to='products/', null=True, blank=True)
    image_2 = models.ImageField(upload_to='products/', null=True, blank=True)
    image_3 = models.ImageField(upload_to='products/', null=True, blank=True)
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='otro')
    is_available = models.BooleanField(default=True, verbose_name="Disponible en stock")

    def __str__(self):
        return self.name

    @property
    def is_express_active(self):
        if self.is_express_promo and self.express_promo_end:
            return timezone.now() <= self.express_promo_end
        return False

    def activate_express_promo(self, hours=24):
        self.is_express_promo = True
        self.express_promo_start = timezone.now()
        self.express_promo_end = timezone.now() + timedelta(hours=hours)
        self.save()

    @property
    def is_featured_active(self):
        if self.is_featured and self.featured_until:
            return timezone.now() <= self.featured_until
        return False

    def activate_featured_promo(self, days=7):
        self.is_featured = True
        self.featured_until = timezone.now() + timedelta(days=days)
        self.save()

    @property
    def discount_percentage(self):
        if self.promo_price and self.price and self.price > 0 and self.promo_price < self.price:
            discount = ((self.price - self.promo_price) / self.price) * 100
            return round(discount)
        return 0
    

# ==========================================
# MODELO DE RESEÑAS Y VALORACIONES
# ==========================================
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author_name = models.CharField(max_length=50, default="Vecino Anónimo")
    rating = models.IntegerField(choices=[(i, f"{i} Estrellas") for i in range(1, 6)], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐ por {self.author_name}"


# ==========================================
# MODELO DE FAVORITOS (CLIENTES)
# ==========================================
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} -> {self.product.name}"
