from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView, View
)

from .forms import ReviewForm, ProfileForm
from .models import Category, User, Product, Review, Favorite, ShoppingCart


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


class ShoppingCartFavoriteMixin:
    """Миксин для добавления/удаления избранного/коризины."""

    def post(self, request, product_id, model=None):
        product = get_object_or_404(Product, id=product_id)
        existing_item = model.objects.filter(
            user=request.user, product=product)
        if existing_item.exists():
            existing_item.delete()
        else:
            model.objects.create(user=request.user, product=product)
        return redirect(request.META.get(
            'HTTP_REFERER', redirect(
                'product:product_detail', product_id=product_id
            )
        ))


class ShoppingCartFavoriteListMixin:
    """Миксин для получения избранного/корзины пользователя."""

    def get_queryset(self, model=None):
        return model.objects.filter(
            user=self.request.user,
        ).select_related('product')


class FavoriteCartContextMixin:
    """Миксин для добавления избранного/корзины в контекст."""

    def get_items(self, model):
        return model.objects.filter(
            user=self.request.user,
        ).values_list('product_id', flat=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            favorites_ids = self.get_items(Favorite)
            context['favorite_ids'] = set(favorites_ids)
            cart_ids = self.get_items(ShoppingCart)
            context['cart_ids'] = set(cart_ids)
        return context


class IndexView(ListView):
    """Главная станица."""

    model = Category
    context_object_name = 'categories'
    template_name = 'product/index.html'

    def get_queryset(self):
        return Category.objects.filter(is_published=True)


class CategoryListView(FavoriteCartContextMixin, ListView):
    """Представление товаров этой категории."""

    model = Product
    template_name = 'product/category.html'
    context_object_name = 'products'

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_queryset(self):
        self._category = self.get_category()
        queryset = Product.objects.filter(
            is_published=True,
            category__is_published=True,
            category=self._category
        )
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                name__icontains=search_query
            )
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, category=self._category)


class ProductDetail(FavoriteCartContextMixin, DetailView):
    """Представление отдельного товара."""

    model = Product
    template_name = 'product/detail.html'
    pk_url_kwarg = 'product_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['reviews'] = product.reviews.all().select_related('author')
        if self.request.user.is_authenticated:
            user_review = product.reviews.filter(
                author=self.request.user).first()
            context['user_review'] = user_review
            context['has_user_reviewed'] = user_review is not None
        else:
            context['has_user_reviewed'] = False
        if not context.get('has_user_reviewed'):
            context['form'] = ReviewForm()
        return context


class ReviewCreateView(AuthRequiredMixin, CreateView):
    """Представление страницы создания отзывов."""

    model = Review
    form_class = ReviewForm
    template_name = 'product/detail.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=self.kwargs['product_id'])
        if Review.objects.filter(
            author=self.request.user, product=self.product
        ).exists():
            messages.warning(request, 'Вы уже оставили отзыв на этот товар.')
            return redirect(
                'product:product_detail', product_id=self.product.id
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            form.instance.author = self.request.user
            form.instance.product = self.product
            form.save()
            messages.success(self.request, 'Спасибо за ваш отзыв!')
        except IntegrityError:
            messages.error(
                self.request, 'Вы уже оставили отзыв на этот товар.')
            return redirect(
                'product:product_detail', product_id=self.product.id
            )
        return redirect('product:product_detail', product_id=self.product.id)


class ReviewUpdateView(ReviewCRUDMixin, OnlyAuthorMixin, UpdateView):
    """Представление страницы изменения отзыва."""

    form_class = ReviewForm


class ReviewDeleteView(ReviewCRUDMixin, OnlyAuthorMixin, DeleteView):
    """Представление страницы удаления отзыва."""


class ProfileListView(ListView):
    """Представлние страницы профиля пользователя."""

    model = Review
    template_name = 'product/profile.html'

    def get_author(self):
        return get_object_or_404(
            User, username=self.kwargs['username']
        )

    def get_queryset(self):
        self._author = self.get_author()
        return Review.objects.filter(
            author=self._author,
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            profile=self._author,
            is_owner=self.request.user == self._author
        )


class ProfileUpdateView(AuthRequiredMixin, UpdateView):
    """Представление страницы редактирования профиля пользователя"""

    model = User
    form_class = ProfileForm
    template_name = 'product/user.html'
    success_url = reverse_lazy('product:profile')

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse('product:profile', args=[self.request.user.username])


class ToggleFavoriteView(ShoppingCartFavoriteMixin, View):
    """Представления для удаления/добавления в избранное."""

    def post(self, request, product_id):
        return super().post(request, product_id, Favorite)


class ToggleShoppingCartView(ShoppingCartFavoriteMixin, View):
    """Представления для удаления/добавления в корзину."""

    def post(self, request, product_id):
        return super().post(request, product_id, ShoppingCart)


class FavoriteListView(
    AuthRequiredMixin, ShoppingCartFavoriteListMixin,
    FavoriteCartContextMixin, ListView
):
    """Представление для всех избранных товаров пользователя."""

    model = Favorite
    template_name = 'product/favorite.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return super().get_queryset(Favorite)


class ShoppingCartListView(
    AuthRequiredMixin, ShoppingCartFavoriteListMixin,
    FavoriteCartContextMixin, ListView
):
    """Представление для всех товаров добавленных в корзину пользователем."""

    model = ShoppingCart
    template_name = 'product/shopping_cart.html'
    context_object_name = 'shopping_carts'

    def get_queryset(self):
        return super().get_queryset(ShoppingCart)

    def get_context_data(self, **kwargs):
        cart_items = self.get_queryset()
        selected_items = [item for item in cart_items if item.is_selected]
        return super().get_context_data(
            **kwargs,
            total_price=sum(
                item.product.price
                if not item.product.is_sale else item.product.sale_price
                for item in selected_items
            ),
            selected_count=len(selected_items),
        )


class UpdateCartSelectionView(AuthRequiredMixin, View):
    """Представления для добавления товаров для оформления заказа."""

    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        selected_products = [int(p_id) for p_id in selected_products]
        cart_items = ShoppingCart.objects.filter(user=request.user)
        for item in cart_items:
            if item.product.id in selected_products:
                item.is_selected = True
            else:
                item.is_selected = False
            item.save(update_fields=['is_selected'])
        return redirect('product:shopping_cart')


class RemoveSelectedCartView(AuthRequiredMixin, View):
    """Представлние для удаления выбранных товаров."""

    def pos(self, request):
        ShoppingCart.objects.filter(
            user=request.user,
            is_selected=True
        ).delete()
        return redirect('product:shopping_cart')
