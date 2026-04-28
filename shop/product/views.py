from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from .forms import ProfileForm, ReviewForm
from .mixins import (
    AuthRequiredMixin,
    CartMixin,
    FavoriteCartContextMixin,
    FavoriteMixin,
    OnlyAuthorMixin,
    ReviewCRUDMixin,
    ShoppingCartFavoriteMixin,
)
from .models import CartProduct, Category, Favorite, Product, Review, User


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
            in_stock=True,
            category__is_published=True,
            category=self._category
        ).prefetch_related('reviews')
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                name__icontains=search_query
            )
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self._category
        for product in context['products']:
            reviews = product.reviews.all()
            if reviews:
                product.average_rating = sum(
                    rating.rating for rating in reviews) / len(reviews)
            else:
                product.average_rating = 0
        return context


class ProductDetail(FavoriteCartContextMixin, DetailView):
    """Представление отдельного товара."""

    model = Product
    template_name = 'product/detail.html'
    pk_url_kwarg = 'product_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        all_reviews = product.reviews.all()
        context['reviews'] = all_reviews.select_related('author')
        if all_reviews:
            average_rating = sum(
                review.rating for review in all_reviews) / len(all_reviews)
        else:
            average_rating = 0
        context['avarege_rating'] = average_rating
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


class ToggleFavoriteView(AuthRequiredMixin, ShoppingCartFavoriteMixin, View):
    """Представления для удаления/добавления в избранное."""

    def post(self, request, product_id):
        self.toggle_favorite(request, product_id)
        return redirect(
            request.META.get(
                'HTTP_REFERER', reverse(
                    'product:product_detail', args=[product_id]
                )))


class ToggleShoppingCartView(
    AuthRequiredMixin, ShoppingCartFavoriteMixin, View
):
    """Представления для удаления/добавления в корзину."""

    def post(self, request, product_id):
        self.toggle_cart(request, product_id)
        return redirect(
            request.META.get(
                'HTTP_REFERER', reverse(
                    'product:product_detail', args=[product_id]
                )))


class FavoriteListView(
    AuthRequiredMixin, FavoriteCartContextMixin, FavoriteMixin, ListView
):
    """Представление для всех избранных товаров пользователя."""

    model = Favorite
    template_name = 'product/favorite.html'
    context_object_name = 'favorites'

    def get_queryset(self):
        return self.get_favorites()


class ShoppingCartListView(
    AuthRequiredMixin, FavoriteCartContextMixin, CartMixin, ListView
):
    """Представление для всех товаров добавленных в корзину пользователем."""

    template_name = 'product/shopping_cart.html'
    context_object_name = 'cart_products'

    def get_queryset(self):
        return self.get_cart_products()

    def get_context_data(self, **kwargs):
        cart_items = self.get_queryset()
        selected_items = [item for item in cart_items if item.is_selected]
        return super().get_context_data(
            **kwargs,
            total_price=sum(
                item.product.price
                if not item.product.is_sale else item.product.sale_price
                * item.quantity
                for item in selected_items
            ),
            selected_count=sum(
                item.quantity for item in cart_items if item.is_selected
            ),
        )


class UpdateCartSelectionView(AuthRequiredMixin, CartMixin, View):
    """Представления для добавления товаров для оформления заказа."""

    def post(self, request):
        selected_products = request.POST.getlist('selected_products')
        selected_products = [int(p_id) for p_id in selected_products]
        cart_items = self.get_cart_products()
        for item in cart_items:
            item.is_selected = item.product.id in selected_products
            item.save(update_fields=['is_selected'])
        return redirect('product:shopping_cart')


class RemoveSelectedCartView(AuthRequiredMixin, CartMixin, View):
    """Представлние для удаления выбранных товаров."""

    def post(self, request):
        cart_products = self.get_cart_products()
        selected_items = cart_products.filter(is_selected=True)
        selected_items.delete()
        cart = self.get_user_cart()
        if cart and not cart_products.exists():
            cart.delete()
        return redirect('product:shopping_cart')


class QuantityProductUpdate(AuthRequiredMixin, CartMixin, View):
    """Представления для изменения кол-ва товаров в корзине."""

    def post(self, request, product_id):
        quantity = int(request.POST.get('quantity'))
        cart = self.get_user_cart()
        if cart:
            cart_item = CartProduct.objects.get(
                cart=cart, product_id=product_id)
            if (cart_item.quantity != quantity and
                    quantity <= cart_item.product.max_quantity):
                cart_item.quantity = quantity
                cart_item.save()

        return redirect('product:shopping_cart')
