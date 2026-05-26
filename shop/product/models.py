from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

RATING_CHOICES = [
    (1, '1 - Ужасно'),
    (2, '2 - Плохо'),
    (3, '3 - Нормально'),
    (4, '4 - Хорошо'),
    (5, '5 - Отлично'),
]

ORDER_STATUS_CHOICES = [
    ('paid', 'Оплачен'),
    ('collecting', 'Собирается на складе'),
    ('pick_up', 'Можно забирать'),
    ('shipped', 'Доставлен'),  # на будущее (доставка)
    ('cancelled', 'Отменен'),
]


class PublishedModel(models.Model):
    """Абстрактная модель. Добвляет флаг created_at."""

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено')

    class Meta:
        abstract = True


User = get_user_model()


class Category(PublishedModel):
    """Категории."""

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    name = models.CharField('Название', max_length=256)
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text=('Идентификатор страницы для URL; '
                   'разрешены символы латиницы, цифры, дефис и подчёркивание.')
    )
    image = models.ImageField('Картинка', upload_to='category_image')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(PublishedModel):
    """Товары."""

    name = models.CharField('Название', max_length=256, unique=True)
    price = models.IntegerField('Цена', validators=[MinValueValidator(0),])
    description = models.TextField('Описание', null=True, blank=True)
    size = models.CharField('Размер', max_length=256, null=True, blank=True)
    color = models.CharField('Цвет', max_length=256, null=True, blank=True)
    material = models.CharField(
        'Материал', max_length=256, null=True, blank=True
    )
    category = models.ForeignKey(
        Category, verbose_name='Категория',
        on_delete=models.CASCADE, related_name='category'
    )
    in_stock = models.BooleanField(
        'В наличии', default=True,
        help_text='Снимите галочку, если товар закончился'
    )
    max_quantity = models.IntegerField('Кол-во товара', default=1)
    is_sale = models.BooleanField('На распродаже', default=False)
    sale_price = models.IntegerField(
        'Цена со скидкой', validators=[MinValueValidator(0)],
        null=True, blank=True
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name[:15]


class Gallery(PublishedModel):
    """Изображения."""

    image = models.ImageField(
        'Картинка', upload_to='good_image', null=False, blank=False
    )
    product = models.ForeignKey(
        Product, verbose_name='Товар',
        on_delete=models.CASCADE, related_name='images')

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'

    def __str__(self):
        return f'для {self.product.name}'


class Review(models.Model):
    """Отзывы."""

    text = models.TextField('Отзыв')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    product = models.ForeignKey(
        Product, verbose_name='Товар',
        on_delete=models.CASCADE, related_name='reviews'
    )
    author = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.IntegerField('Оценка', choices=RATING_CHOICES, default=5)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'product'],
                name='unique_review'
            )
        ]

    def __str__(self):
        return f'Отзыв от {self.author.username} на {self.product.name}'


class Favorite(models.Model):
    """Избранное."""

    user = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE, related_name='favorites'
    )
    product = models.ForeignKey(
        Product, verbose_name='Товар',
        on_delete=models.CASCADE, related_name='favorites'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_favorites'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.product}'


class ShoppingCart(models.Model):
    """Корзина покупок."""

    user = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE, related_name='carts'
    )
    products = models.ManyToManyField(
        Product, through='CartProduct',
        verbose_name='Товары', related_name='carts'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_user_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.products}'


class CartProduct(models.Model):
    """Корзина пользователя с кол-вом товаров."""

    cart = models.ForeignKey(
        ShoppingCart, on_delete=models.CASCADE,
        related_name='cart_products', verbose_name='Корзина'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='cart_products', verbose_name='Товар'
    )
    quantity = models.IntegerField(
        'Количество', validators=[MinValueValidator(1),], default=1
    )
    is_selected = models.BooleanField('Купить', default=True)

    class Meta:
        verbose_name = 'Корзина с количеством'
        verbose_name_plural = 'Корзины с количеством'
        unique_together = ('cart', 'product')

    def __str__(self):
        return (f'{self.product.name}, {self.quantity} шт.')


class Order(PublishedModel):
    """Заказы."""

    user = models.ForeignKey(
        User, verbose_name='Пользователь',
        on_delete=models.CASCADE, related_name='orders'
    )
    email = models.EmailField('Email', max_length=254, blank=True)
    first_name = models.CharField('Имя', max_length=50)
    last_name = models.CharField('Фамилия', max_length=50)
    phone = models.CharField('Номер телефона', max_length=20)
    address = models.CharField('Адрес', max_length=254)  # для будущего
    total_price = models.IntegerField('Итоговая сумма')
    status = models.CharField(
        'Статус', max_length=50,
        choices=ORDER_STATUS_CHOICES, default='paid'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Заказ №{self.id} от {self.user.username}'
