from django.db import models

class Business(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    whatsapp = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('abarrotes', 'Abarrotes'),
        ('refacciones', 'Refacciones y Autos'),
        ('comida', 'Comida y Antojitos'),
        ('servicios', 'Servicios y Oficios'),
        ('otro', 'Otro'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_promo = models.BooleanField(default=False)
    promo_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='otro')

    def __str__(self):
        return self.name

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    author_name = models.CharField(max_length=50, default="Vecino Anónimo")
    rating = models.IntegerField(choices=[(i, f"{i} Estrellas") for i in range(1, 6)], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐ por {self.author_name}"
