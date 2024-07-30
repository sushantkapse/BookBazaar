"""
URL configuration for bookstore_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from bookstore import views
from django.conf.urls.static import static

from bookstore.views import  AddReview, AdminOrdersView, BookDetailView, CategoryBooksView, MonthlySalesReportView, OrderConfirmation, OrderDeleteView, OrderDetailView,  Orders,  RegisterView,LoginView, SalesReportDownloadView, SalesReportView, UpdateCartView, UserHomeView,LogoutView,AdminHomeView,EditBookView,DeleteBookView,AddToCartView,CartView,RemoveFromCartView,CheckoutView, generate_invoice, generate_monthly_report

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user_home/', UserHomeView.as_view(), name='user_home'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin_home/', AdminHomeView.as_view(), name='admin_home'),
     path('confirm_order/<int:order_id>/', AdminHomeView.as_view(), name='order_confirm'),

    path('admin_add_category/', views.AddCategoryView.as_view(), name='admin_add_category'),
    path('admin_add_book/', views.AddBookView.as_view(), name='admin_add_book'),
    path('admin_category_list/', views.CategoryListView.as_view(), name='admin_category_list'),
    path('admin_book_list/', views.BookListView.as_view(), name='admin_book_list'),
     path('admin_delete_category/<int:pk>/', views.DeleteCategoryView.as_view(), name='admin_delete_category'),
    path('admin_edit_category/<int:pk>/', views.EditCategoryView.as_view(), name='admin_edit_category'),
     path('admin_edit_book/<int:pk>/', EditBookView.as_view(), name='admin_edit_book'),
     path('admin_delete_book/<int:pk>/', DeleteBookView.as_view(), name='admin_delete_book'),

    # path('user_dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    # path('category/<id:id>/', CategoryBooksView.as_view(), name='category_books'),
    path('category/<int:id>/', CategoryBooksView.as_view(), name='category_books'),

    # path('category/<int:id>/', CategoryBooksView.as_view(), name='category_books'),
    path('add-to-cart/<int:id>/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', CartView.as_view(), name='cart'),
     path('remove-from-cart/<int:id>/', RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('update-cart/<int:item_id>/', UpdateCartView.as_view(), name='update_cart'),
   
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-confirmation/<int:order_id>/', OrderConfirmation.as_view(),name='order_confirmation'),
    path('orders/', Orders.as_view(),name='orders'),
    path('delete_order/<int:order_id>/', OrderDeleteView.as_view(), name='delete_order'),

    path('admin_orders/', AdminOrdersView.as_view(), name='admin_orders'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    #  path('rate_book/<int:book_id>/', RateBookView.as_view(), name='rate_book'),

    # path('rate_book/<int:book_id>/', RateBookView.as_view(), name='rate_book'),
    path('book/<int:book_id>/', BookDetailView.as_view(), name='book_detail'),
    #  path('add_review/<int:book_id>/', AddReview.as_view(), name='add_review'),
    path('add_review/<int:book_id>/', AddReview.as_view(), name='add_review'),
    #  path('order/<int:order_id>/invoice/', OrderInvoiceView.as_view(), name='order_invoice'),
    path('invoice/<int:order_id>/', generate_invoice, name='order_invoice'),
    path('sales_report/', SalesReportView.as_view(), name='sales_report'),
    path('download-sales-report/', SalesReportDownloadView.as_view(), name='download_sales_report'),
     path('monthly-sales-report/', MonthlySalesReportView.as_view(), name='monthly_sales_report'),
    
    #  path('download_monthly_sales_report/', generate_pdf, name='download_monthly_sales_report'),
    path('download_monthly_report/', generate_monthly_report, name='download_monthly_report'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


