from django.urls import path
# Importamos las vistas de nuestra aplicación para poder enlazarlas
from . import views

urlpatterns = [
    # Ruta de la página principal / mapa de productos cercanos
    path('', views.nearby_products_view, name='home'),
    
    # Rutas de autenticación y panel del negocio
    path('login/', views.business_login_view, name='business_login'),
    path('logout/', views.business_logout_view, name='business_logout'),
    path('register/', views.register_business_view, name='register_business'),
    path('dashboard/', views.business_dashboard_view, name='business_dashboard'),
    path('add-product/', views.add_product_view, name='add_product'),
    
    # Ruta para agregar reseñas a los productos
    path('product/<int:product_id>/review/', views.add_review_view, name='add_review'),
    
    # Nueva ruta para restablecer la contraseña al instante desde el login
    path('recuperar-password/', views.reset_password_direct_view, name='reset_password_direct'),

    path('product/<int:product_id>/toggle-express/', views.toggle_express_promo_view, name='toggle_express_promo'),
    path('product/<int:product_id>/update-promo/', views.update_promo_price_view, name='update_promo_price'),

    path('product/<int:product_id>/edit/', views.edit_product_view, name='edit_product'),

    path('product/<int:product_id>/', views.product_detail_view, name='product_detail'),

    path('business/<int:business_id>/', views.business_profile_view, name='business_profile'),   
]
