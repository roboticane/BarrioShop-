import json
from django.contrib.auth.decorators import login_required
# Añadimos get_user_model para poder consultar el modelo de usuarios dinámicamente
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from math import radians, sin, cos, sqrt, atan2
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages


# Modelos y Formularios del sistema
from .models import Product, Business, Review
from .forms import BusinessForm, BusinessRegistrationForm, ProductForm, ReviewForm

# ==========================================
# FUNCIÓN DE CÁLCULO DE DISTANCIA (Haversine)
# ==========================================
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos 
    utilizando sus coordenadas de latitud y longitud.
    """
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# ==========================================
# VISTA PRINCIPAL (INICIO Y MAPA DE CERCANÍA)
# ==========================================
def nearby_products_view(request):
    """
    Vista principal de BarrioShop.
    - Si se selecciona una categoría, muestra todos los productos de esa categoría.
    - Si se escribe en el buscador, filtra por texto.
    - Si no hay filtros, muestra los productos cercanos (radio de 5 km).
    - Carga también las Ofertas Exprés activas (vigencia 24 hrs) para el banner superior.
    """
    DEFAULT_LAT = 19.0413
    DEFAULT_LNG = -98.2062

    lat_param = request.GET.get('lat')
    lng_param = request.GET.get('lng')

    # Validación de coordenadas para Puebla
    if lat_param and lng_param:
        try:
            user_lat = float(lat_param)
            user_lng = float(lng_param)
            if abs(user_lat - DEFAULT_LAT) > 0.5 or abs(user_lng - DEFAULT_LNG) > 0.5:
                return redirect('home')
        except ValueError:
            user_lat = DEFAULT_LAT
            user_lng = DEFAULT_LNG
    else:
        user_lat = DEFAULT_LAT
        user_lng = DEFAULT_LNG
    
    max_distance_km = 5.0
    query = request.GET.get('q', '').strip()
    selected_category = request.GET.get('category', '').strip()

    nearby_items = []
    businesses_dict = {}

    # ==========================================
    # CASO 1: EL USUARIO FILTRÓ POR CATEGORÍA
    # ==========================================
    if selected_category:
        filtered_products = Product.objects.select_related('business').filter(category=selected_category)

        for product in filtered_products:
            b = product.business
            distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
            product.distance_km = round(distance, 1)
            nearby_items.append(product)

            if b.id not in businesses_dict:
                businesses_dict[b.id] = {
                    'name': b.name, 'address': b.address,
                    'lat': b.latitude, 'lng': b.longitude, 'whatsapp': b.whatsapp
                }

    # ==========================================
    # CASO 2: EL USUARIO ESCRIBIÓ ALGO EN EL BUSCADOR
    # ==========================================
    elif query:
        filtered_products = Product.objects.select_related('business').filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(business__name__icontains=query)
        )

        for product in filtered_products:
            b = product.business
            distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
            product.distance_km = round(distance, 1)
            nearby_items.append(product)

            if b.id not in businesses_dict:
                businesses_dict[b.id] = {
                    'name': b.name, 'address': b.address,
                    'lat': b.latitude, 'lng': b.longitude, 'whatsapp': b.whatsapp
                }

    # ==========================================
    # CASO 3: VISTA NORMAL POR CERCANÍA (SIN FILTROS)
    # ==========================================
    else:
        all_products = Product.objects.select_related('business').all()

        for product in all_products:
            b = product.business
            distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
            
            if distance <= max_distance_km:
                product.distance_km = round(distance, 1)
                nearby_items.append(product)

                if b.id not in businesses_dict:
                    businesses_dict[b.id] = {
                        'name': b.name, 'address': b.address,
                        'lat': b.latitude, 'lng': b.longitude, 'whatsapp': b.whatsapp
                    }

    # Ordenamos los resultados por cercanía
    nearby_items = sorted(nearby_items, key=lambda x: x.distance_km)

    # ==========================================
    # CARGAR PROMOCIONES EXPRÉS ACTIVAS (24 HORAS)
    # ==========================================
    express_promos = []
    active_express_products = Product.objects.select_related('business').filter(
        is_express_promo=True,
        express_promo_end__gt=timezone.now()
    )

    for prod in active_express_products:
        b = prod.business
        distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
        if distance <= 5.0:  # Solo negocios cercanos con oferta exprés
            prod.distance_km = round(distance, 1)
            express_promos.append(prod)

    # Preparamos el contexto completo para la plantilla HTML
    context = {
        'products': nearby_items,
        'query': query,
        'selected_category': selected_category,
        'express_promos': express_promos,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'businesses_json': json.dumps(list(businesses_dict.values())),
    }
    return render(request, 'marketplace/index.html', context)

# ==========================================
# VISTA DE REGISTRO DE NUEVA EMPRESA
# ==========================================
def register_business_view(request):
    if request.method == 'POST':
        form = BusinessRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save()
            login(request, business.user)
            return redirect('business_dashboard')
    else:
        form = BusinessRegistrationForm()
    
    return render(request, 'marketplace/register.html', {'form': form})

# ==========================================
# VISTA PARA PUBLICAR NUEVOS PRODUCTOS
# ==========================================
@login_required(login_url='business_login')
def add_product_view(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('register_business')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = business
            product.save()
            return redirect('business_dashboard')
    else:
        form = ProductForm()
        form.fields['business'].queryset = Business.objects.filter(id=business.id)
        form.fields['business'].initial = business
    
    return render(request, 'marketplace/add_product.html', {'form': form})

# ==========================================
# VISTA DE INICIO DE SESIÓN PARA NEGOCIOS
# ==========================================
def business_login_view(request):
    User = get_user_model()
    error_message = None

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user_obj = User.objects.filter(
            Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
        ).first()

        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('business_dashboard')
            else:
                error_message = "La contraseña es incorrecta. Por favor verifica tus datos."
        else:
            error_message = "No encontramos ninguna cuenta registrada con ese usuario o correo."
    else:
        form = AuthenticationForm()

    return render(request, 'marketplace/login.html', {
        'form': form,
        'error_message': error_message
    })

# ==========================================
# VISTA DE CIERRE DE SESIÓN
# ==========================================
def business_logout_view(request):
    logout(request)
    return redirect('home')

# ==========================================
# PANEL DE ADMINISTRACIÓN DEL NEGOCIO
# ==========================================
@login_required(login_url='business_login')
def business_dashboard_view(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('register_business')
    
    products = Product.objects.filter(business=business)
    
    active_express_count = products.filter(
        is_express_promo=True,
        express_promo_end__gt=timezone.now()
    ).count()
    
    context = {
        'business': business,
        'products': products,
        'active_express_count': active_express_count,
    }
    return render(request, 'marketplace/dashboard.html', context)

# ==========================================
# VISTA PARA AGREGAR RESEÑAS A PRODUCTOS
# ==========================================
def add_review_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.save()
    return redirect('home')

# ==========================================
# ACTIVAR / DESACTIVAR PROMOCIÓN EXPRÉS (24H)
# ==========================================
@login_required(login_url='business_login')
def toggle_express_promo_view(request, product_id):
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)

    if not product.is_express_active:
        active_promos_count = Product.objects.filter(
            business=business, 
            is_express_promo=True, 
            express_promo_end__gt=timezone.now()
        ).count()

        if active_promos_count >= 3:
            messages.error(request, "⚠️ Límite alcanzado: Solo puedes tener hasta 3 Promociones Exprés activas simultáneamente (24 hrs).")
        else:
            product.activate_express_promo(hours=24)
            messages.success(request, f"⚡ ¡Promoción Exprés activada para '{product.name}'! Estará visible por 24 horas.")
    else:
        product.is_express_promo = False
        product.save()
        messages.info(request, f"Promoción Exprés desactivada para '{product.name}'.")

    return redirect('business_dashboard')

# ==========================================
# ACTUALIZAR PRECIO DE OFERTA RELÁMPAGO
# ==========================================
@login_required(login_url='business_login')
def update_promo_price_view(request, product_id):
    """Permite al vendedor guardar el precio de oferta con descuento para su producto."""
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)
    
    if request.method == 'POST':
        promo_price = request.POST.get('promo_price')
        if promo_price:
            try:
                product.promo_price = float(promo_price)
                product.save()
                messages.success(request, f"💰 Precio de oferta actualizado para '{product.name}'.")
            except ValueError:
                messages.error(request, "⚠️ Ingrese un valor numérico válido para el precio.")
        else:
            product.promo_price = None
            product.save()
            messages.info(request, f"Precio de oferta removido de '{product.name}'.")
            
    return redirect('business_dashboard')

# ==========================================
# VISTA PARA RESTABLECER CONTRASEÑA DIRECTAMENTE
# ==========================================
def reset_password_direct_view(request):
    error_message = None
    success_message = None

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not new_password or not confirm_password:
            error_message = "Por favor llena todos los campos de contraseña."
        elif new_password != confirm_password:
            error_message = "Las nuevas contraseñas no coinciden."
        else:
            user_obj = User.objects.filter(
                Q(username__iexact=identifier) | Q(email__iexact=identifier)
            ).first()

            if user_obj:
                user_obj.set_password(new_password)
                user_obj.save()
                success_message = "¡Contraseña actualizada con éxito! Ya puedes iniciar sesión con tu nueva clave."
            else:
                error_message = "No encontramos ninguna cuenta con ese usuario o correo electrónico."

    return render(request, 'marketplace/login.html', {
        'form': AuthenticationForm(),
        'reset_error': error_message,
        'reset_success': success_message,
        'show_reset_form': True
    })

# ==========================================
# VISTA PARA EDITAR UN PRODUCTO EXISTENTE
# ==========================================
@login_required(login_url='business_login')
def edit_product_view(request, product_id):
    """Permite al comerciante modificar los datos, fotos y condición de su producto."""
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"✨ ¡El producto '{product.name}' ha sido actualizado con éxito!")
            return redirect('business_dashboard')
    else:
        form = ProductForm(instance=product)
        # Ocultamos o restringimos el selector de negocio al propio negocio logueado
        form.fields['business'].queryset = Business.objects.filter(id=business.id)

    return render(request, 'marketplace/edit_product.html', {'form': form, 'product': product})

# ==========================================
# VISTA DE DETALLE DEL PRODUCTO (GALERÍA 3 FOTOS)
# ==========================================
def product_detail_view(request, product_id):
    """Muestra la página de detalle de un producto con sus hasta 3 fotografías y condición."""
    DEFAULT_LAT = 19.0413
    DEFAULT_LNG = -98.2062
    
    product = get_object_or_404(Product.objects.select_related('business'), id=product_id)
    
    # Calculamos la distancia al negocio
    b = product.business
    lat_param = request.GET.get('lat', DEFAULT_LAT)
    lng_param = request.GET.get('lng', DEFAULT_LNG)
    try:
        user_lat = float(lat_param)
        user_lng = float(lng_param)
    except ValueError:
        user_lat = DEFAULT_LAT
        user_lng = DEFAULT_LNG
        
    distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
    product.distance_km = round(distance, 1)

    return render(request, 'marketplace/product_detail.html', {'product': product})


def business_profile_view(request, business_id):
    """Muestra el perfil público de un negocio y todos sus productos activos."""
    DEFAULT_LAT = 19.0413
    DEFAULT_LNG = -98.2062
    
    # Obtenemos el negocio o error 404 si no existe
    business = get_object_or_404(Business, id=business_id)
    
    # Obtenemos todos los productos de este negocio específico
    products = Product.objects.filter(business=business).order_by('-id')
    
    # Calculamos la distancia respecto al usuario
    lat_param = request.GET.get('lat', DEFAULT_LAT)
    lng_param = request.GET.get('lng', DEFAULT_LNG)
    try:
        user_lat = float(lat_param)
        user_lng = float(lng_param)
    except ValueError:
        user_lat = DEFAULT_LAT
        user_lng = DEFAULT_LNG
        
    distance = calculate_distance(user_lat, user_lng, business.latitude, business.longitude)
    business.distance_km = round(distance, 1)
    
    # Asignamos la distancia a cada producto para mantener la coherencia visual
    for p in products:
        p.distance_km = business.distance_km

    context = {
        'business': business,
        'products': products,
        'user_lat': user_lat,
        'user_lng': user_lng,
    }
    return render(request, 'marketplace/business_profile.html', context)
