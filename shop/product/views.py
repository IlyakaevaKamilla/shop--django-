from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
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


class IndexView(ListView):
    """Главная станица."""

    model = Category
    context_object_name = 'categories'
    template_name = 'product/index.html'

    def get_queryset(self):
        return Category.objects.filter(is_published=True)


class CategoryListView(ListView):
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


class ProductDetail(DeleteView):
    """Представление отдельного товара."""

    model = Product
    template_name = 'product/detail.html'
    pk_url_kwarg = 'product_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['reviews'] = product.reviews.all().select_related('author')
        if self.request.user.is_authenticated:
            user_review = product.reviews.filter(author=self.request.user).first()
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
            return redirect('product:product_detail', product_id=self.product.id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            form.instance.author = self.request.user
            form.instance.product = self.product
            form.save()
            messages.success(self.request, 'Спасибо за ваш отзыв!')
        except IntegrityError:
            messages.error(self.request, 'Вы уже оставили отзыв на этот товар.')
            return redirect('product:product_detail', pk=self.product.id)
        return redirect('product:product_detail', pk=self.product.id)

    # def get_success_url(self):
    #     return reverse(
    #         'product:product_detail', args=[self.kwargs['product_id']]
    #     )


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
