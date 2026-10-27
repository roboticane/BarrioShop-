from django.urls import path
from .views import (
    nearby_products_view, 
    register_business_view, 
    add_product_view, 
    business_login_view, 
    business_logout_view, 
    business_dashboard_view,
    add_review_view  # <-- Importamos la vista de reseñas
)

urlpatterns = [
    path('', nearby_products_view, name='home'),
    path('register/', register_business_view, name='register_business'),
    path('add-product/', add_product_view, name='add_product'),
    path('login/', business_login_view, name='business_login'),
    path('logout/', business_logout_view, name='business_logout'),
    path('dashboard/', business_dashboard_view, name='business_dashboard'),
    path('review/<int:product_id>/', add_review_view, name='add_review'), # <-- Nueva ruta

]
