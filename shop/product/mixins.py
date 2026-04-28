from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from .models import CartProduct, Favorite, Product, Review, ShoppingCart


class AuthRequiredMixin(LoginRequiredMixin):
    """Миксин для проверки аутентификации"""

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return redirect('shop:index')
        return super().handle_no_permission()


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для проверки авторства"""

    def test_func(self):
        return self.get_object().author == self.request.user


class ReviewCRUDMixin:
    """Миксин для представлений операций CRUD с отзывами."""

    model = Review
    pk_url_kwarg = 'review_id'
    template_name = 'product/review.html'

    def get_success_url(self):
        return reverse(
            'product:product_detail', args=[self.kwargs['product_id']]
        )


class CartMixin:
    """Миксин для получения корзины пользователя."""

    def get_user_cart(self):
        return ShoppingCart.objects.filter(user=self.request.user).first()

    def get_cart_products(self):
        cart = self.get_user_cart()
        if cart:
            return CartProduct.objects.filter(
                cart=cart
            ).select_related('product')
        return CartProduct.objects.none()

    def get_cart_product_ids(self):
        return self.get_cart_products().values_list('product_id', flat=True)


class FavoriteMixin:
    """Миксин для работы с избранным."""

    def get_favorites(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related('product')

    def get_favorite_ids(self):
        return self.get_favorites().values_list('product_id', flat=True)


class FavoriteCartContextMixin(CartMixin, FavoriteMixin):
    """Миксин для добавления избранного/корзины в контекст."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['favorite_ids'] = set(self.get_favorite_ids())
            context['cart_ids'] = set(self.get_cart_product_ids())
        return context


class ShoppingCartFavoriteMixin:
    """Миксин для добавления/удаления избранного/коризины."""

    def toggle_favorite(self, request, product_id):
        """Изменить избранное."""
        product = get_object_or_404(Product, id=product_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, product=product
        )
        if not created:
            favorite.delete()

    def toggle_cart(self, request, product_id):
        """Изменить корзину."""
        product = get_object_or_404(Product, id=product_id)
        cart, _ = ShoppingCart.objects.get_or_create(user=request.user)
        cart_item = CartProduct.objects.filter(cart=cart, product=product)
        if cart_item.exists():
            cart_item.delete()
            if not CartProduct.objects.filter(cart=cart).exists():
                cart.delete()
        else:
            CartProduct.objects.create(cart=cart, product=product)
