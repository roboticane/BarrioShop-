import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import IntegrityError, transaction
from math import radians, sin, cos, sqrt, atan2
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse

from .models import Product, Business, Review, Favorite, PurchaseCode
from .forms import BusinessForm, BusinessRegistrationForm, ProductForm, ReviewForm

MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"

# ==========================================
# VISTA PARA ROBOTS.TXT (SEO BÚSQUEDAS)
# ==========================================
def robots_txt_view(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Allow: /business/",
        "Allow: /barrioshop/",
        "Disallow: /dashboard/",
        "Disallow: /cliente/",
        "Disallow: /login/",
        "Disallow: /register/",
        "Disallow: /add-product/",
        "Disallow: /mis-favoritos/",
        "Disallow: /recuperar-password/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

# ==========================================
# FUNCIÓN DE CÁLCULO DE DISTANCIA (Haversine)
# ==========================================
def calculate_distance(lat1, lon1, lat2, lon2):
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
    DEFAULT_LAT = 19.0413
    DEFAULT_LNG = -98.2062

    lat_param = request.GET.get('lat')
    lng_param = request.GET.get('lng')

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

    if selected_category:
        filtered_products = Product.objects.select_related('business').filter(
            category=selected_category, 
            business__is_active=True,
            is_available=True
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

    elif query:
        filtered_products = Product.objects.select_related('business').filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(business__name__icontains=query),
            business__is_active=True,
            is_available=True
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

    else:
        all_products = Product.objects.select_related('business').filter(
            business__is_active=True,
            is_available=True
        )

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

    nearby_items = sorted(
        nearby_items, 
        key=lambda x: (not x.is_featured_active, x.distance_km)
    )

    express_promos = []
    active_express_products = Product.objects.select_related('business').filter(
        is_express_promo=True,
        express_promo_end__gt=timezone.now(),
        business__is_active=True,
        is_available=True
    )

    for prod in active_express_products:
        b = prod.business
        distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
        if distance <= 5.0:
            prod.distance_km = round(distance, 1)
            express_promos.append(prod)

    user_favorite_ids = []
    if request.user.is_authenticated:
        user_favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'products': nearby_items,
        'query': query,
        'selected_category': selected_category,
        'express_promos': express_promos,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'businesses_json': json.dumps(list(businesses_dict.values())),
        'user_favorite_ids': user_favorite_ids,
    }
    return render(request, 'marketplace/index.html', context)


# ==========================================
# VISTA DE REGISTRO DE NUEVA EMPRESA
# ==========================================
def register_business_view(request):
    already_logged_in = request.user.is_authenticated

    if request.method == 'POST':
        form = BusinessRegistrationForm(
            request.POST,
            request.FILES,
            user=request.user if already_logged_in else None,
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    business = form.save()
                if not already_logged_in:
                    login(request, business.user, backend=MODEL_BACKEND)
                messages.success(request, "¡Tu negocio ha sido registrado con éxito!")
                return redirect('dashboard')
            except IntegrityError:
                messages.error(request, "⚠️ El nombre de usuario o correo electrónico ya se encuentra registrado o el usuario ya tiene un negocio asociado.")
        else:
            messages.error(request, "⚠️ Por favor corrige los errores en el formulario.")
    else:
        form = BusinessRegistrationForm(user=request.user if already_logged_in else None)
    
    return render(request, 'marketplace/register.html', {'form': form})


# ==========================================
# VISTA PARA PUBLICAR NUEVOS PRODUCTOS (Con Límite por Plan)
# ==========================================
@login_required(login_url='business_login')
def add_product_view(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('register_business')

    # 🌟 VALIDACIÓN DE LÍMITE DE PRODUCTOS SEGÚN EL PLAN
    current_products_count = Product.objects.filter(business=business).count()
    if current_products_count >= business.max_products_allowed:
        messages.error(
            request, 
            f"⚠️ Has alcanzado el límite de {business.max_products_allowed} productos de tu {business.get_plan_display()}. ¡Mejora tu plan para publicar más!"
        )
        return redirect('dashboard')

    can_installments = bool(business.is_active and business.plan in ['pro', 'estrella'])

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, business=business)
        if form.is_valid():
            product = form.save(commit=False)
            product.business = business
            product.save()
            messages.success(request, f"✨ ¡El producto '{product.name}' ha sido publicado con éxito!")
            return redirect('dashboard')
    else:
        form = ProductForm(business=business)
        form.fields['business'].queryset = Business.objects.filter(id=business.id)
        form.fields['business'].initial = business
    
    return render(request, 'marketplace/add_product.html', {
        'form': form,
        'business': business,
        'can_installments': can_installments,
    })


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
                login(request, user, backend=getattr(user, "backend", MODEL_BACKEND))
                return redirect('dashboard')
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
# VISTA PARA AGREGAR RESEÑAS A PRODUCTOS (Compra Verificada)
# ==========================================
def add_review_view(request, product_id):
    product = get_object_or_404(Product.objects.select_related('business'), id=product_id)

    if request.method == 'POST':
        code_input = request.POST.get('purchase_code', '').strip().upper()
        form = ReviewForm(request.POST)

        if not code_input:
            messages.error(request, "⚠️ Debes ingresar el código de compra que te dio el vendedor para opinar.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        purchase_code = PurchaseCode.objects.filter(
            code=code_input,
            business=product.business,
            is_used=False
        ).filter(
            Q(product__isnull=True) | Q(product=product)
        ).first()

        if not purchase_code:
            messages.error(request, "⚠️ El código de compra no es válido, ya fue utilizado o no corresponde a este negocio/producto.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        if form.is_valid():
            with transaction.atomic():
                review = form.save(commit=False)
                review.product = product
                review.purchase_code = purchase_code
                review.save()

                purchase_code.is_used = True
                purchase_code.used_at = timezone.now()
                purchase_code.save()

            messages.success(request, "✅ ¡Gracias! Tu opinión de compra verificada se publicó con éxito.")
        else:
            messages.error(request, "⚠️ Revisa los datos de tu calificación e intenta de nuevo.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ==========================================
# GENERAR CÓDIGO DE COMPRA VERIFICADA DESDE EL PANEL
# ==========================================
@login_required(login_url='business_login')
def generate_purchase_code_view(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('register_business')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = None
        if product_id:
            product = Product.objects.filter(id=product_id, business=business).first()

        purchase_code = PurchaseCode.objects.create(
            business=business,
            product=product,
        )
        messages.success(request, f"🎟️ Código generado: {purchase_code.code}")

    return redirect('dashboard')


# ==========================================
# ACTIVAR / DESACTIVAR PROMOCIÓN EXPRÉS (Con Límite por Plan)
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

        # 🌟 USAMOS EL LÍMITE DINÁMICO SEGÚN EL PLAN DEL NEGOCIO
        if active_promos_count >= business.max_express_promos_allowed:
            messages.error(request, f"⚠️ Límite alcanzado: Tu {business.get_plan_display()} permite máximo {business.max_express_promos_allowed} Promoción(es) Exprés activa(s).")
        else:
            product.activate_express_promo(hours=24)
            messages.success(request, f"⚡ ¡Promoción Exprés activada para '{product.name}'!")
    else:
        product.is_express_promo = False
        product.save()
        messages.info(request, f"Promoción Exprés desactivada para '{product.name}'.")

    return redirect('dashboard')


# ==========================================
# ACTUALIZAR PRECIO DE OFERTA RELÁMPAGO
# ==========================================
@login_required(login_url='business_login')
def update_promo_price_view(request, product_id):
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
                messages.error(request, "⚠️ Ingrese un valor numérico válido.")
        else:
            product.promo_price = None
            product.save()
            messages.info(request, f"Precio de oferta removido de '{product.name}'.")
            
    return redirect('dashboard')


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
                success_message = "¡Contraseña actualizada con éxito!"
            else:
                error_message = "No encontramos ninguna cuenta con ese usuario o correo."

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
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)
    can_installments = bool(business.is_active and business.plan in ['pro', 'estrella'])

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, business=business)
        if form.is_valid():
            form.save()
            messages.success(request, f"✨ ¡El producto '{product.name}' ha sido actualizado!")
            return redirect('dashboard')
    else:
        form = ProductForm(instance=product, business=business)
        form.fields['business'].queryset = Business.objects.filter(id=business.id)

    return render(request, 'marketplace/edit_product.html', {
        'form': form,
        'product': product,
        'business': business,
        'can_installments': can_installments,
    })


# ==========================================
# VISTA DE DETALLE DEL PRODUCTO (Con Slug de Negocio y Producto)
# ==========================================
def product_detail_view(request, business_slug, product_slug):
    DEFAULT_LAT = 19.0413
    DEFAULT_LNG = -98.2062

    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    product = get_object_or_404(
        Product.objects.select_related('business'),
        business=business,
        slug=product_slug,
    )

    if not product.is_available:
        return redirect('home')

    lat_param = request.GET.get('lat', DEFAULT_LAT)
    lng_param = request.GET.get('lng', DEFAULT_LNG)
    try:
        user_lat = float(lat_param)
        user_lng = float(lng_param)
    except ValueError:
        user_lat = DEFAULT_LAT
        user_lng = DEFAULT_LNG

    distance = calculate_distance(user_lat, user_lng, business.latitude, business.longitude)
    product.distance_km = round(distance, 1)

    return render(request, 'marketplace/product_detail.html', {
        'product': product,
        'business': business,
    })


# ==========================================
# VISTA DE PERFIL PÚBLICO DEL NEGOCIO (Con Slug)
# ==========================================
def business_profile_view(request, business_slug):
    DEFAULT_LAT = 19.0413
    DEFAULT_LNG = -98.2062
    
    business = get_object_or_404(Business, slug=business_slug, is_active=True)
    products = Product.objects.filter(business=business, is_available=True).order_by('-id')
    
    products = sorted(products, key=lambda x: not x.is_featured_active)
    
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
    
    for p in products:
        p.distance_km = business.distance_km

    user_favorite_ids = []
    if request.user.is_authenticated:
        user_favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'business': business,
        'products': products,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'user_favorite_ids': user_favorite_ids,
    }
    return render(request, 'marketplace/business_profile.html', context)


# ==========================================
# DESACTIVAR CUENTA DESDE EL PANEL
# ==========================================
@login_required(login_url='business_login')
def deactivate_business_view(request):
    if request.method == 'POST':
        try:
            business = request.user.business
            business.is_active = False
            business.save()
            logout(request)
            messages.success(request, "Tu cuenta ha sido desactivada correctamente.")
        except Business.DoesNotExist:
            pass
    return redirect('home')


# ==========================================
# VISTA PARA ELIMINAR UN PRODUCTO
# ==========================================
@login_required(login_url='business_login')
def delete_product_view(request, product_id):
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f"🗑️ El producto '{product_name}' ha sido eliminado.")
        
    return redirect('dashboard')


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
    
    total_products_count = products.count()
    active_express_count = products.filter(
        is_express_promo=True,
        express_promo_end__gt=timezone.now()
    ).count()
    
    promo_prices_count = sum(1 for p in products if p.promo_price is not None and str(p.promo_price).strip() != '')
    purchase_codes = PurchaseCode.objects.filter(business=business).select_related('product').order_by('-created_at')[:15]
    
    context = {
        'business': business,
        'products': products,
        'active_express_count': active_express_count,
        'total_products_count': total_products_count,
        'promo_prices_count': promo_prices_count,
        'purchase_codes': purchase_codes,
    }
    return render(request, 'marketplace/dashboard.html', context)


# ==========================================
# ALTERNAR ESTADO DE STOCK
# ==========================================
@login_required(login_url='business_login')
def toggle_stock_view(request, product_id):
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)
    
    product.is_available = not product.is_available
    product.save()
    
    if product.is_available:
        messages.success(request, f"✅ El producto '{product.name}' está Disponible.")
    else:
        messages.warning(request, f"📦 El producto '{product.name}' está Agotado.")
        
    return redirect('dashboard')


# ==========================================
# VISTA PARA EDITAR EL PERFIL DEL NEGOCIO
# ==========================================
@login_required(login_url='business_login')
def edit_business_profile_view(request):
    business = get_object_or_404(Business, user=request.user)

    if request.method == 'POST':
        form = BusinessForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "✨ ¡Datos del negocio actualizados con éxito!")
            return redirect('dashboard')
        else:
            messages.error(request, "⚠️ Por favor corrige los errores en el formulario.")
    else:
        form = BusinessForm(instance=business)

    context = {
        'form': form,
        'business': business,
    }
    return render(request, 'marketplace/edit_business.html', context)


# ==========================================
# ACTIVAR / DESACTIVAR DESTACADO SEMANAL
# ==========================================
@login_required(login_url='business_login')
def toggle_featured_view(request, product_id):
    business = request.user.business
    product = get_object_or_404(Product, id=product_id, business=business)

    if not product.is_featured_active:
        product.activate_featured_promo(days=7)
        messages.success(request, f"⭐ ¡'{product.name}' es Producto Destacado por 7 días!")
    else:
        product.is_featured = False
        product.featured_until = None
        product.save()
        messages.info(request, f"Se desactivó el destacado para '{product.name}'.")

    return redirect('dashboard')


# ==========================================
# VISTAS DE AUTENTICACIÓN Y GESTIÓN DE FAVORITOS (CLIENTES)
# ==========================================
def customer_register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend=MODEL_BACKEND)
            next_url = request.GET.get('next') or 'my_favorites'
            return redirect(next_url)
    else:
        form = UserCreationForm()
    return render(request, 'marketplace/customer_auth.html', {'form': form, 'is_register': True})

def customer_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend=getattr(user, "backend", MODEL_BACKEND))
            next_url = request.GET.get('next') or 'my_favorites'
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'marketplace/customer_auth.html', {'form': form, 'is_register': False})

def customer_logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='customer_login')
def toggle_favorite_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        favorite.delete()
        messages.info(request, f"Se quitó '{product.name}' de tus favoritos.")
    else:
        messages.success(request, f"❤️ ¡Guardaste '{product.name}' en tus favoritos!")
        
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='customer_login')
def my_favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product', 'product__business')
    return render(request, 'marketplace/my_favorites.html', {'favorites': favorites})

# ==========================================
# VISTA DE PLANES Y PRECIOS PARA NEGOCIOS
# ==========================================
@login_required(login_url='business_login')
def plans_pricing_view(request):
    try:
        business = request.user.business
    except Business.DoesNotExist:
        return redirect('register_business')

    context = {
        'business': business,
    }
    return render(request, 'marketplace/plans.html', context)
