from django.urls import path

from . import views

app_name = 'product'

urlpatterns = [
    path('products/<int:product_id>/',
         views.ProductDetail.as_view(), name='product_detail'),
    path('category/<slug:category_slug>/',
         views.CategoryListView.as_view(), name='category'),
    path('products/<int:product_id>/review/',
         views.ReviewCreateView.as_view(), name='add_review'),
    path('products/<int:product_id>/edit_review/<int:review_id>',
         views.ReviewUpdateView.as_view(), name='edit_review'),
    path('products/<int:product_id>/delete_review/<int:review_id>',
         views.ReviewDeleteView.as_view(), name='delete_review'),
    path('profile/edit/',
         views.ProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/<str:username>/',
         views.ProfileListView.as_view(), name='profile'),
    path('toggle-favorite/<int:product_id>/',
         views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('toggle-cart/<int:product_id>/',
         views.ToggleShoppingCartView.as_view(), name='toggle_shopping_cart'),
    path('favorites/', views.FavoriteListView.as_view(), name='favoriites'),
    path('shopping-cart/',
         views.ShoppingCartListView.as_view(), name='shopping_cart'),
    path('shopping-cart/update/<int:product_id>/',
         views.QuantityProductUpdate.as_view(), name='update_quantity'),
    path('shopping-cart/update-selection',
         views.UpdateCartSelectionView.as_view(), name='update_selection'),
    path('shopping-cart/delete-selection',
         views.RemoveSelectedCartView.as_view(), name='remove_selected'),
    path('', views.IndexView.as_view(), name='index'),
]
