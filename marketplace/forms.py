from django import forms
from django.contrib.auth.models import User
from .models import Business, Product, Review

# ==========================================
# 1. FORMULARIO DE REGISTRO DE NUEVO NEGOCIO
# ==========================================
class BusinessRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=False,
        label="Nombre de usuario para acceso",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Ej. abarrotes_don_jose'
        })
    )

    password = forms.CharField(
        required=False,
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '••••••••'
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        self.existing_user = user if (user and getattr(user, "is_authenticated", False)) else None
        super().__init__(*args, **kwargs)

        if self.existing_user:
            # Si ya inició sesión como comprador, no necesita crear otro usuario ni contraseña
            self.fields.pop('username', None)
            self.fields.pop('password', None)
        else:
            self.fields['username'].required = True
            self.fields['password'].required = True

    def clean_username(self):
        if self.existing_user:
            return None
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise forms.ValidationError("Ingresa un nombre de usuario.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_password(self):
        if self.existing_user:
            return None
        password = self.cleaned_data.get('password') or ''
        if not password:
            raise forms.ValidationError("Ingresa una contraseña.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        if self.existing_user and Business.objects.filter(user=self.existing_user).exists():
            raise forms.ValidationError(
                "Tu cuenta ya tiene un negocio registrado. Solo se permite un negocio por cuenta."
            )
        return cleaned_data

    class Meta:
        model = Business
        fields = [
            'name',
            'logo',
            'description',
            'whatsapp',
            'address',
            'business_type',
            'delivery_zones',
            'work_days',
            'opening_time',
            'closing_time',
            'saturday_opening_time',
            'saturday_closing_time',
            'sunday_opening_time',
            'sunday_closing_time',
            'latitude',
            'longitude'
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 5212221234567'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'business_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'delivery_zones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2, 'placeholder': 'Ej. Entregas en Walmart San Manuel'}),
            'work_days': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. Lunes a Sábado (Descansamos domingos)'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'saturday_opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'saturday_closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'sunday_opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'sunday_closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
        }

    def save(self, commit=True):
        business = super().save(commit=False)

        if self.existing_user:
            user = self.existing_user
        else:
            username = self.cleaned_data['username']
            password = self.cleaned_data['password']
            user = User.objects.create_user(username=username, password=password)

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
        fields = [
            'name',
            'logo',
            'description',
            'whatsapp',
            'address',
            'business_type',
            'delivery_zones',
            'work_days',
            'opening_time',
            'closing_time',
            'saturday_opening_time',
            'saturday_closing_time',
            'sunday_opening_time',
            'sunday_closing_time',
            'latitude',
            'longitude'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. 5212221234567'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'business_type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'delivery_zones': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'rows': 2}),
            'work_days': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'placeholder': 'Ej. Lunes a Sábado (Descansamos domingos)'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'saturday_opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'saturday_closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'sunday_opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'sunday_closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'latitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500', 'step': 'any'}),
        }


# ==========================================
# 3. FORMULARIO DE PRODUCTOS
# ==========================================
class ProductForm(forms.ModelForm):
    def __init__(self, *args, business=None, **kwargs):
        self.business = business or getattr(kwargs.get('instance'), 'business', None)
        super().__init__(*args, **kwargs)

        can_installments = bool(
            self.business
            and self.business.is_active
            and self.business.plan in ['pro', 'estrella']
        )

        if not can_installments:
            self.fields['installment_months'].disabled = True
            self.fields['installment_interest_free'].disabled = True
            self.fields['installment_months'].help_text = "Disponible en Plan Barrio Pro y Plan Negocio Estrella."

    def clean(self):
        cleaned_data = super().clean()
        can_installments = bool(
            self.business
            and self.business.is_active
            and self.business.plan in ['pro', 'estrella']
        )

        if not can_installments:
            cleaned_data['installment_months'] = 0
            cleaned_data['installment_interest_free'] = False
        elif not cleaned_data.get('installment_months'):
            cleaned_data['installment_months'] = 0
            cleaned_data['installment_interest_free'] = False

        return cleaned_data

    class Meta:
        model = Product
        fields = [
            'business', 'name', 'description', 'warranty', 'price',
            'condition', 'is_promo', 'promo_price',
            'installment_months', 'installment_interest_free',
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
            'installment_months': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'}),
            'installment_interest_free': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
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
