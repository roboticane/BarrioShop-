import json
from django.shortcuts import render, redirect
from django.db.models import Q
from math import radians, sin, cos, sqrt, atan2

# 1. Los modelos van desde .models
from .models import Product, Business, Review

# 2. Los formularios van desde .forms
from .forms import BusinessForm, ProductForm, ReviewForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def nearby_products_view(request):
    user_lat = float(request.GET.get('lat', 19.0413))
    user_lng = float(request.GET.get('lng', -98.2062))
    max_distance_km = 5.0
    
    query = request.GET.get('q', '')

    products = Product.objects.select_related('business').all()
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(business__name__icontains=query)
        )

    nearby_items = []
    businesses_dict = {}

    for product in products:
        b = product.business
        distance = calculate_distance(user_lat, user_lng, b.latitude, b.longitude)
        
        if distance <= max_distance_km:
            product.distance_km = round(distance, 1)
            nearby_items.append(product)

            # Guardar lista única de negocios cercanos para el mapa
            if b.id not in businesses_dict:
                businesses_dict[b.id] = {
                    'name': b.name,
                    'address': b.address,
                    'lat': b.latitude,
                    'lng': b.longitude,
                    'whatsapp': b.whatsapp
                }

    nearby_items = sorted(nearby_items, key=lambda x: x.distance_km)

    context = {
        'products': nearby_items,
        'query': query,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'businesses_json': json.dumps(list(businesses_dict.values())),
    }
    return render(request, 'marketplace/index.html', context)

def register_business_view(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = BusinessForm()
    
    return render(request, 'marketplace/register.html', {'form': form})

def add_product_view(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductForm()
    
    return render(request, 'marketplace/add_product.html', {'form': form})

def business_login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('business_dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'marketplace/login.html', {'form': form})

def business_logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='business_login')
def business_dashboard_view(request):
    # Aquí puedes asociar el negocio al usuario logueado en un futuro. 
    # Por ahora, mostramos todos los productos para que el dueño los gestione.
    products = Product.objects.all()
    return render(request, 'marketplace/dashboard.html', {'products': products})

def add_review_view(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.save()
    return redirect('home')
