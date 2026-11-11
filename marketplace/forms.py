from django import forms
from django.contrib.auth.models import User
from .models import Business, Product, Review

# ==========================================
# 1. FORMULARIO DE REGISTRO DE NUEVO NEGOCIO
# ==========================================
class BusinessRegistrationForm(forms.ModelForm):
    # Campo personalizado (no está directo en el modelo Business) para crear el usuario de acceso
    username = forms.CharField(
        max_length=150, 
        label="Nombre de usuario para acceso",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 
            'placeholder': 'Ej. abarrotes_don_jose'
        })
    )
    
    # Campo personalizado para la contraseña (oculta los caracteres por seguridad)
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = Business  # Conecta este formulario directamente con la base de datos de Negocios
        
        # Lista de campos que se mostrarán en la pantalla de registro (incluyendo los dos nuevos)
        fields = [
            'name', 
            'description', 
            'whatsapp', 
            'address', 
            'business_type',   # Nuevo: Permite elegir si es local físico o entrega en puntos
            'delivery_zones',  # Nuevo: Especifica dónde entrega si no tiene local fijo
            'latitude', 
            'longitude'
        ]
        
        # Diccionario con estilos de diseño Tailwind CSS y ayudas visuales para el usuario
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 5212221234567'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            
            # Estilos para los selectores de tipo de negocio y zonas de entrega
            'business_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'delivery_zones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2, 'placeholder': 'Ej. Entregas en Walmart San Manuel y Paseo Bravo'}),
            
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
        }

    def save(self, commit=True):
        """
        Sobrescribimos el método save() para automatizar dos acciones clave al registrarse:
        1. Crear el usuario de Django cifrando su contraseña.
        2. Guardar el negocio y asignarle automáticamente ese usuario creado.
        """
        # 1. Extraemos los datos validados de usuario y contraseña
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        
        # Creamos el registro del usuario en la base de datos de autenticación
        user = User.objects.create_user(username=username, password=password)

        # 2. Preparamos el guardado del negocio sin escribirlo aún en la BD (commit=False)
        business = super().save(commit=False)
        
        # Vinculamos la tienda con el usuario recién generado
        business.user = user
        
        # Si commit es True, guardamos definitivamente el negocio con todos sus datos nuevos
        if commit:
            business.save()
            
        return business


# ==========================================
# 2. FORMULARIO DE EDICIÓN DE NEGOCIO
# ==========================================
class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        # Permite actualizar los datos del negocio, incluyendo tipo y zonas de entrega
        fields = ['name', 'description', 'whatsapp', 'address', 'business_type', 'delivery_zones', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 5212221234567'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'business_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'delivery_zones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
        }


# ==========================================
# 3. FORMULARIO DE PRODUCTOS (ACTUALIZADO CON GARANTÍA)
# ==========================================
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'business', 'name', 'description', 'warranty', 'price',  # 🛡️ Añadido warranty aquí
            'condition', 'is_promo', 'promo_price', 
            'image', 'image_2', 'image_3', 'category'
        ]
        widgets = {
            'business': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'warranty': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 30 días de garantía con el vendedor'}), # 🛡️ Estilo para garantía
            'price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'condition': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'is_promo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
            'promo_price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'image': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
            'image_2': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
            'image_3': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
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
