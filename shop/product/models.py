from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


class PublishedModel(models.Model):
    """Абстрактная модель. Добвляет флаг is_published, created_at."""

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name='Добавлено')

    class Meta:
        abstract = True


User = get_user_model()


class Category(PublishedModel):
    """Категории."""

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
    image = models.ImageField('Картинка', upload_to='good_image')
    category = models.ForeignKey(
        Category, verbose_name='Категория',
        on_delete=models.CASCADE, related_name='category'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name[:15]


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
    # можно попробовать добавить оценку (от 1 до 5)

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


class ProductUser(models.Model):
    """Абстрактная модель связ товар-пользователь."""

    user = models.ForeignKey(
        User, verbose_name='Автор',
        on_delete=models.CASCADE, related_name='%(class)ss'
    )
    product = models.ForeignKey(
        Product, verbose_name='Товар',
        on_delete=models.CASCADE, related_name='%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.product}'


class Favorite(ProductUser):
    """Избранное."""

    class Meta(ProductUser.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'


class ShoppingCart(ProductUser):
    """Корзина покупок."""

    class Meta(ProductUser.Meta):
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
