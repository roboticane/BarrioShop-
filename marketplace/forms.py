from django import forms
from django.contrib.auth.models import User
from .models import Business, Product, Review

# ==========================================
# 1. FORMULARIO DE REGISTRO DE NUEVO NEGOCIO
# ==========================================
class BusinessRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150, 
        label="Nombre de usuario para acceso",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 
            'placeholder': 'Ej. abarrotes_don_jose'
        })
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = Business
        fields = [
            'name', 
            'description', 
            'whatsapp', 
            'address', 
            'business_type',   
            'delivery_zones',  
            'opening_time',    
            'closing_time',    
            'latitude', 
            'longitude'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 5212221234567'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'business_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'delivery_zones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2, 'placeholder': 'Ej. Entregas en Walmart San Manuel'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
        }

    def save(self, commit=True):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        user = User.objects.create_user(username=username, password=password)
        business = super().save(commit=False)
        business.user = user
        if commit:
            business.save()
        return business


# ==========================================
# 2. FORMULARIO DE EDICIÓN DE NEGOCIO
# ==========================================
class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'description', 'whatsapp', 'address', 'business_type', 'delivery_zones', 'opening_time', 'closing_time', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 5212221234567'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'business_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'delivery_zones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
        }


# ==========================================
# 3. FORMULARIO DE PRODUCTOS
# ==========================================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'business', 'name', 'description', 'warranty', 'price',  
            'condition', 'is_promo', 'promo_price', 
            'image', 'image_2', 'image_3', 'category'
        ]
        widgets = {
            'business': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'warranty': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 30 días de garantía'}), 
            'price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'condition': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'is_promo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
            'promo_price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500'}),
            'image_2': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500'}),
            'image_3': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
        }


# ==========================================
# 4. FORMULARIO DE RESEÑAS
# ==========================================
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['author_name', 'rating', 'comment']
        widgets = {
            'author_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Tu nombre'}),
            'rating': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'comment': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2, 'placeholder': 'Escribe tu opinión...'}),
        }
