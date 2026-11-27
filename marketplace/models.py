import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta
from decimal import Decimal
from django.db.models import Avg

# ==========================================
# MODELO DE NEGOCIOS / TIENDAS
# ==========================================
class Business(models.Model):
    BUSINESS_TYPE_CHOICES = [
        ('fisico', 'Local Físico / Tienda Establecida'),
        ('entrega', 'Entregas en Puntos / Puntos Medios'),
    ]

    PLAN_CHOICES = [
        ('free', 'Plan Vecino (Gratis)'),
        ('pro', 'Plan Barrio Pro'),
        ('estrella', 'Plan Negocio Estrella'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=150)
    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True, verbose_name="Logotipo de la Empresa")
    description = models.TextField()
    whatsapp = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    business_type = models.CharField(max_length=20, choices=BUSINESS_TYPE_CHOICES, default='fisico')
    delivery_zones = models.TextField(blank=True, null=True, help_text="Específica dónde entregas si no tienes local fijo")
    
    work_days = models.CharField(max_length=150, default="Lunes a Sábado", blank=True, null=True, verbose_name="Días de labor / Atención")

    opening_time = models.TimeField(null=True, blank=True, verbose_name="Apertura (Lun - Vie)")
    closing_time = models.TimeField(null=True, blank=True, verbose_name="Cierre (Lun - Vie)")

    saturday_opening_time = models.TimeField(null=True, blank=True, verbose_name="Apertura (Sábado)")
    saturday_closing_time = models.TimeField(null=True, blank=True, verbose_name="Cierre (Sábado)")

    sunday_opening_time = models.TimeField(null=True, blank=True, verbose_name="Apertura (Domingo)")
    sunday_closing_time = models.TimeField(null=True, blank=True, verbose_name="Cierre (Domingo)")

    is_active = models.BooleanField(default=True, verbose_name="¿Empresa Activa?")

    # 🌟 NUEVOS CAMPOS PARA PLANES Y SUSCRIPCIÓN
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free', verbose_name="Plan Actual")
    plan_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Plan Vence El")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    # 🌟 MÉTODOS Y LÍMITES SEGÚN EL PLAN
    @property
    def max_products_allowed(self):
        if self.plan == 'pro':
            return 50
        elif self.plan == 'estrella':
            return 999999 # Ilimitados
        return 10 # Plan Free / Vecino por defecto

    @property
    def max_express_promos_allowed(self):
        if self.plan == 'pro':
            return 5
        elif self.plan == 'estrella':
            return 999999 # Ilimitadas
        return 1 # Plan Free (1 activa a la vez)

    def get_today_schedule(self):
        """Retorna una tupla (apertura, cierre) correspondiente al día de la semana actual."""
        weekday = timezone.localtime().weekday()
        if weekday == 5:
            return (self.saturday_opening_time, self.saturday_closing_time)
        elif weekday == 6:
            return (self.sunday_opening_time, self.sunday_closing_time)
        else:
            return (self.opening_time, self.closing_time)

    @property
    def is_open_now(self):
        now = timezone.localtime()
        current_time = now.time()
        weekday = now.weekday()

        op_time, cl_time = self.get_today_schedule()

        if weekday in [5, 6] and (not op_time or not cl_time):
            if self.opening_time and self.closing_time:
                return False
            return None

        if not op_time or not cl_time:
            return None

        if op_time <= cl_time:
            return op_time <= current_time <= cl_time
        else:
            return current_time >= op_time or current_time <= cl_time

    @property
    def today_hours_display(self):
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

    INSTALLMENT_CHOICES = [
        (0, 'Sin meses / Pago de contado'),
        (3, '3 meses'),
        (6, '6 meses'),
        (9, '9 meses'),
        (12, '12 meses'),
        (18, '18 meses'),
        (24, '24 meses'),
    ]

    business = models.ForeignKey('Business', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='nuevo')
    warranty = models.CharField(max_length=255, blank=True, null=True, verbose_name="Garantía del producto", help_text="Ej. Sin garantía, 30 días con el vendedor, etc.")
    search_tags = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Etiquetas de búsqueda",
        help_text="Máximo 3 etiquetas separadas por coma (ej. moneda, mundial 2026, coleccionable)"
    )

    is_promo = models.BooleanField(default=False)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # 🌟 PROMOCIÓN A MESES (PLAN BARRIO PRO Y PLAN NEGOCIO ESTRELLA)
    installment_months = models.PositiveSmallIntegerField(
        choices=INSTALLMENT_CHOICES,
        default=0,
        verbose_name="Promoción a meses"
    )
    installment_interest_free = models.BooleanField(
        default=True,
        verbose_name="¿Sin intereses?"
    )
    
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

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        self.is_promo = bool(
            self.promo_price is not None
            and self.price is not None
            and self.promo_price > 0
            and self.promo_price < self.price
        )
        super().save(*args, **kwargs)

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

    @property
    def can_use_installments(self):
        return bool(
            self.business
            and self.business.is_active
            and self.business.plan in ['pro', 'estrella']
            and (self.installment_months or 0) > 0
        )

    @property
    def monthly_installment_amount(self):
        if not self.can_use_installments:
            return None
        has_valid_discount = (
            self.promo_price is not None
            and self.price is not None
            and self.promo_price > 0
            and self.promo_price < self.price
        )
        base_price = self.promo_price if has_valid_discount else self.price
        if not base_price or self.installment_months <= 0:
            return None
        return (Decimal(base_price) / Decimal(self.installment_months)).quantize(Decimal('0.01'))

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(avg=Avg('rating'))['avg']
        if avg is None:
            return "0.0"
        return f"{avg:.1f}"


# ==========================================
# CÓDIGOS DE COMPRA VERIFICADA POR NEGOCIO
# ==========================================
class PurchaseCode(models.Model):
    business = models.ForeignKey('Business', on_delete=models.CASCADE, related_name='purchase_codes')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_codes')
    code = models.CharField(max_length=24, unique=True)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = secrets.token_hex(4).upper()  # Ej. 8F3A9C12
        else:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        estado = "Usado" if self.is_used else "Disponible"
        return f"{self.code} - {self.business.name} ({estado})"


# ==========================================
# MODELO DE RESEÑAS Y VALORACIONES
# ==========================================
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    purchase_code = models.OneToOneField(
        PurchaseCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='review'
    )
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
