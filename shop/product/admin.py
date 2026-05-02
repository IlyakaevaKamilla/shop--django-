from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    Category,
    Gallery,
    Product,
    Review,
    Order
)


class ImageInline(admin.StackedInline):
    model = Gallery
    extra = 1


class ReviewInLine(admin.TabularInline):
    model = Review
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = (ImageInline, ReviewInLine)
    list_display = (
        'name', 'price', 'category', 'max_quantity', 'favorites_count',
        'cart_count', 'in_stock', 'is_sale', 'sale_price'
    )
    list_editable = (
        'price', 'max_quantity', 'in_stock', 'is_sale', 'sale_price'
    )
    search_fields = ('name',)
    list_filter = ('category',)

    @admin.display(description='В избранном')
    def favorites_count(self, product):
        return product.favorites.count()

    @admin.display(description='В корзине')
    def cart_count(self, product):
        return product.cart_products.count()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'show_image', 'is_published')
    list_editable = ('is_published',)

    @admin.display(description='Изображение')
    @mark_safe
    def show_image(self, category):
        if category.image:
            return (f"<img src='{category.image.url}'"
                    "width='150' style='object-fit: cover;'>")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'first_last_name', 'email', 'phone', 'total_price', 'status'
    )
    list_editable = ('status',)

    @admin.display(description='Фамилия Имя')
    def first_last_name(self, user):
        return f'{user.last_name} {user.first_name}'
