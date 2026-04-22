from django import forms

from .models import Review, User


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ('text',)


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
