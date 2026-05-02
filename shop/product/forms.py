from django import forms

from .models import Review, User, Order


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ('text', 'rating')


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email', 'phone')
