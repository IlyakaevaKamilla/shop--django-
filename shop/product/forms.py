from django import forms

from .models import Review, User, ShoppingCart


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ('text',)


# class ShoppingCartForm(forms.ModelForm):

#     class Meta:
#         model = ShoppingCart
#         fields = ('is_selected',)


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
