from datetime import timezone
import datetime
from django.utils import timezone
from decimal import Decimal
from reportlab.platypus import Paragraph, Spacer
from django.contrib.auth import authenticate, login, logout
from django.http import FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
import matplotlib.pyplot as plt
from django.db.models.functions import ExtractDay
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import io
from io import BytesIO
import base64
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, FormView,DeleteView,UpdateView,ListView
from .models import Category, Book,Cart,CartItem, Order, OrderItem, Rating, Review
from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import DetailView
from django.db.models import Avg
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Order, OrderItem
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.db.models import Sum, Count, Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile




# from bookstore.models import Product, Category


class RegisterView(View):
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
            else:
                user = User.objects.create(username=username, email=email, password=make_password(password1))
                messages.success(request, f'Account created for {username}! You can now log in.')
                request.session['username'] = username  # Store username in session
                return redirect('login')  # Redirect to login page after successful registration
        else:
            messages.error(request, 'Passwords do not match')

        return render(request, self.template_name)


class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session['username'] = username  # Store username in session
            if user.is_superuser:
                # Redirect to admin dashboard or specific admin page
                return redirect('admin_home')
            else:
                # Redirect to user dashboard or specific user page
                return redirect('user_home')
        else:
            messages.error(request, 'Invalid username or password')

        return render(request, self.template_name)

@method_decorator(staff_member_required, name='dispatch')
class AdminHomeView(View):
    template_name = 'admin_home.html'

    def get(self, request):
        total_books = Book.objects.count()
        total_orders = Order.objects.count()
        total_customers = User.objects.filter(is_staff=False).count()
        orders = Order.objects.filter(is_confirmed=False).order_by('-created_at')

        # Calculate sales
        today = timezone.now()
        daily_sales = Order.objects.filter(created_at__date=today.date()).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        weekly_sales = Order.objects.filter(created_at__gte=today - timezone.timedelta(days=7)).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        monthly_sales = Order.objects.filter(created_at__year=today.year, created_at__month=today.month).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        yearly_sales = Order.objects.filter(created_at__year=today.year).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Add customers and orders of a particular type
        customers = User.objects.filter(is_staff=False)
        # particular_type_orders = Order.objects.filter(order_type='Particular Type')  # Modify this as per your needs

        context = {
            'total_books': total_books,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'orders': orders,
            'daily_sales': daily_sales,
            'weekly_sales': weekly_sales,
            'monthly_sales': monthly_sales,
            'yearly_sales': yearly_sales,
            'customers': customers,
            # 'particular_type_orders': particular_type_orders,
        }
        return render(request, self.template_name, context)

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order.is_confirmed = True
        order.save()
        return redirect('admin_home')

class UserHomeView(View):
    template_name = 'user_home.html'

    def get(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            categories = Category.objects.all()
            books = Book.objects.all()

            for book in books:
                book.average_rating = book.rating_set.aggregate(avg=Avg('rating'))['avg'] or 2.5

            context = {
                'categories': categories,
                'books': books,
            }
            return render(request, self.template_name, context)
        else:
            return redirect('login')

    def post(self, request):
        # Handle post requests if needed
        return render(request, self.template_name)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')
    
class AddCategoryView(View):
    template_name = 'add_category.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        Category.objects.create(name=name)
        return redirect('admin_category_list')

class AddBookView(FormView):
    template_name = 'add_book.html'
    form_class = None  # Define a form class if needed

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        return render(request, self.template_name, {'categories': categories})

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title')
        author = request.POST.get('author')
        category_ids = request.POST.getlist('categories')  # Get list of category IDs
        categories = Category.objects.filter(pk__in=category_ids)
        description = request.POST.get('description')
        price = request.POST.get('price')
        published_date = request.POST.get('published_date')
        image = request.FILES.get('image')

        book = Book.objects.create(
            title=title,
            author=author,
            description=description,
            price=price,
            published_date=published_date,
            image = image
        )
        book.categories.add(*categories)
        return redirect('admin_book_list')

class CategoryListView(TemplateView):
    template_name = 'category_list.html'

    def get(self, request):
        search_query = request.GET.get('search', '')
        if search_query:
            categories = Category.objects.filter(name__icontains=search_query)
        else:
            categories = Category.objects.all()
        return render(request, self.template_name, {'categories': categories, 'search_query': search_query})
    
class DeleteCategoryView(DeleteView):
    model = Category
    success_url = reverse_lazy('admin_category_list')

class EditCategoryView(UpdateView):
    model = Category
    template_name = 'edit_category.html'  # Create this template for editing
    fields = ['name']
    success_url = reverse_lazy('admin_category_list')

class BookListView(TemplateView):
    template_name = 'book_list.html'

    def get(self, request):
        search_query = request.GET.get('search', '')
        if search_query:
            book_list = Book.objects.filter(title__icontains=search_query)
        else:
            book_list = Book.objects.all()
        return render(request, self.template_name, {'book_list': book_list, 'search_query': search_query})
    
class EditBookView(View):
    template_name = 'edit_book.html'

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        categories = Category.objects.all()
        return render(request, self.template_name, {'book': book, 'categories': categories})

    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.description = request.POST.get('description')
        book.price = request.POST.get('price')
        book.published_date = request.POST.get('published_date')

        category_ids = request.POST.getlist('categories')
        categories = Category.objects.filter(pk__in=category_ids)
        book.categories.set(categories)

        book.save()
        return redirect('admin_book_list')

class DeleteBookView(DeleteView):
    model = Book
    template_name = 'delete_book.html'
    success_url = reverse_lazy('admin_book_list')


class CategoryBooksView(ListView):
    template_name = 'category_books.html'
    # context_object_name = 'books'

    def get(self, request, id):
        category = get_object_or_404(Category, id=id)
        books = Book.objects.filter(categories=category)
        print(books)
        print(category)
        return render(request, self.template_name, {'category': category, 'books': books})
      

class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, id):
        book = get_object_or_404(Book, id=id)
       
        cart, created = Cart.objects.get_or_create(user=request.user, active=True)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, book=book)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        return redirect('cart')



class CartView(LoginRequiredMixin, View):
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user, active=True)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items_with_totals = [{'item': item, 'item_total': item.book.price * item.quantity} for item in cart_items]
        total_price = sum(item['item_total'] for item in cart_items_with_totals)
        return render(request, 'cart.html', {'cart_items_with_totals': cart_items_with_totals, 'total_price': total_price})

    
class RemoveFromCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)

class RemoveFromCartView(LoginRequiredMixin, View):
    def post(self, request, id):
        cart = get_object_or_404(Cart, user=request.user, active=True)
        cart_item = get_object_or_404(CartItem, id=id, cart=cart)
        form = RemoveFromCartForm(request.POST)
        if form.is_valid():
            quantity_to_remove = form.cleaned_data['quantity']
            if cart_item.quantity <= quantity_to_remove:
                cart_item.delete()
            else:
                cart_item.quantity -= quantity_to_remove
                cart_item.save()
        return redirect('cart')

class UpdateCartView(View):
    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id)

        new_quantity = int(request.POST['quantity'])
        if new_quantity > 0:
            cart_item.quantity = new_quantity
            cart_item.save()
            # Optionally, you can add a success message here if desired

        # Redirect back to the cart page after updating
        return redirect('cart')




class CheckoutView(View):
    template_name = 'checkout.html'

    def get(self, request):
        try:
            carts = Cart.objects.filter(user=request.user, active=True)
            if carts.count() > 1:
                cart = carts.first()
            else:
                cart = carts.get()
        except Cart.DoesNotExist:
            cart = None

        if not cart or not cart.items.exists():
            return redirect('cart')  # Redirect to cart if it is empty or not found

        cart_items = cart.items.all()
        item_totals = []
        total_price = 0
        for item in cart_items:
            item_total = item.quantity * item.book.price
            item_totals.append({'item': item, 'item_total': item_total})
            total_price += item_total

        return render(request, self.template_name, {
            'cart': cart,
            'cart_items': cart_items,
            'item_totals': item_totals,
            'total_price': total_price,
        })

    def post(self, request):
        try:
            carts = Cart.objects.filter(user=request.user, active=True)
            if carts.count() > 1:
                cart = carts.first()
            else:
                cart = carts.get()
        except Cart.DoesNotExist:
            return redirect('cart')  # Redirect to cart if no cart exists

        cart_items = cart.items.all()
        if not cart_items:
            return redirect('cart')  # Redirect to cart if it is empty

        address_line1 = request.POST.get('address_line1')
        address_line2 = request.POST.get('address_line2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')

        total_amount = Decimal(0)
        for cart_item in cart_items:
            total_amount += cart_item.quantity * cart_item.book.price

        # Create a new order
        order = Order.objects.create(
            user=request.user,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            zip_code=zip_code,
            total_amount=total_amount
        )

        # Move cart items to order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                book=cart_item.book,
                quantity=cart_item.quantity,
                price=cart_item.book.price
            )
            cart_item.delete()  # Remove item from cart

        cart.active = False  # Mark cart as inactive
        cart.save()

        return redirect('order_confirmation', order_id=order.id)


class OrderConfirmation(View):
    template_name = 'order_confirmation.html'

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        order_items = order.items.all()

        for item in order_items:
            item.total_price = item.price * item.quantity

        order_total = sum(item.total_price for item in order_items)

        return render(request, self.template_name, {
            'order': order,
            'order_items': order_items,
            'order_total': order_total,
            'order_status': 'Confirmed' if order.is_confirmed else 'Pending',
        })

class Orders(View):
    template_name = 'orders.html'

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        return render(request, self.template_name, {'orders': orders})
    
class OrderDeleteView(LoginRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.delete()
        return redirect('orders')
    
class AdminOrdersView(View):
    template_name = 'admin_orders.html'

    def get(self, request, *args, **kwargs):
        orders = Order.objects.all()
        context = {
            'orders': orders,
        }
        return render(request, self.template_name, context)
    
class OrderDetailView(DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch related OrderItems and include them in context
        context['ordered_books'] = OrderItem.objects.filter(order=self.object)
        return context


@method_decorator(login_required, name='dispatch')
class AddReview(View):
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if rating and comment:
            try:
                rating_value = float(rating)
                if 0.5 <= rating_value <= 5:
                    Review.objects.create(
                        product=book,
                        customer=request.user,
                        rating=rating_value,
                        comment=comment
                    )
                else:
                    print("Rating out of bounds")
            except ValueError:
                print("Invalid rating value")
        
        return redirect('book_detail', book_id=book_id)

    
class BookDetailView(LoginRequiredMixin, View):
    def get(self, request, book_id):
        product = get_object_or_404(Book, id=book_id)
        reviews = Review.objects.filter(product=product)
        context = {
            'book': product,  # Ensure this matches the template variable
            'reviews': reviews
        }
        return render(request, 'book_detail.html', context)
    

def generate_invoice(request, order_id):
    order = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    pdf.setTitle(f"Invoice #{order_id}")

    styles = getSampleStyleSheet()
    width, height = letter

    # Header
    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColor(colors.HexColor("#4B0082"))
    pdf.drawString(200, height - 70, "Order Invoice")

    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)
    pdf.drawString(30, height - 100, f"Order ID: {order.id}")
    pdf.drawString(30, height - 120, f"Order Date: {order.created_at.strftime('%Y-%m-%d')}")
    pdf.drawString(30, height - 140, f"Status: {'Confirmed' if order.is_confirmed else 'Pending'}")

    # Shipping Address
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, height - 180, "Shipping Address")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(30, height - 200, order.address_line1)
    if order.address_line2:
        pdf.drawString(30, height - 220, order.address_line2)
    pdf.drawString(30, height - 240, f"{order.city}, {order.state} {order.zip_code}")

    # Order Items
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, height - 280, "Items")
    y = height - 300
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, y, "Product")
    pdf.drawString(200, y, "Quantity")
    pdf.drawString(300, y, "Price")
    pdf.drawString(400, y, "Total")

    pdf.line(30, y-5, 500, y-5)
    
    pdf.setFont("Helvetica", 12)
    y -= 20
    for item in order_items:
        pdf.drawString(30, y, item.book.title)
        pdf.drawString(200, y, str(item.quantity))
        pdf.drawString(300, y, f"${item.price:.2f}")
        pdf.drawString(400, y, f"${item.total:.2f}")
        y -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(300, y - 10, "Total")
    pdf.drawString(400, y - 10, f"${order.total_amount:.2f}")

    # Footer
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.gray)
    pdf.drawString(30, 30, "Thank you for your order!")

    pdf.showPage()
    pdf.save()
    
    return response


class SalesReportView(View):
    template_name = 'sales_report.html'

    def get(self, request):
        today = timezone.now()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)

        weekly_data = []
        total_weekly_sales = 0
        total_orders_this_week = 0

        for i in range(7):
            day = start_of_week + timezone.timedelta(days=i)
            day_orders = Order.objects.filter(created_at__date=day.date())
            confirmed_orders = day_orders.filter(is_confirmed=True)
            pending_orders = day_orders.filter(is_confirmed=False)

            daily_sales = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            confirmed_sales = confirmed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            pending_sales = pending_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            weekly_data.append({
                'day': day.strftime('%A'),
                'total_orders': day_orders.count(),
                'pending_orders': pending_orders.count(),
                'confirmed_orders': confirmed_orders.count(),
                'total_sales': daily_sales,
                'confirmed_sales': confirmed_sales,
                'pending_sales': pending_sales
            })

            total_weekly_sales += daily_sales
            total_orders_this_week += day_orders.count()

        # Total Sales for the Month
        start_of_month = today.replace(day=1)
        end_of_month = start_of_month + timezone.timedelta(days=31)  # Assuming a maximum of 31 days in a month
        monthly_sales = Order.objects.filter(created_at__range=[start_of_month, end_of_month]).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Total Sales Overall
        total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Generate graph
        days = [data['day'] for data in weekly_data]
        sales = [data['total_sales'] for data in weekly_data]

        plt.figure(figsize=(10, 5))
        plt.plot(days, sales, marker='o')
        plt.title('Weekly Sales')
        plt.xlabel('Day')
        plt.ylabel('Total Sales')
        plt.grid(True)

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()

        if 'download' in request.GET and request.GET.get('format') == 'pdf':
            return self.get_pdf(request, weekly_data, total_weekly_sales, total_orders_this_week, monthly_sales, total_sales)

        context = {
            'weekly_data': weekly_data,
            'weekly_sales_chart': image_base64,
            'total_weekly_sales': total_weekly_sales,
            'total_orders_this_week': total_orders_this_week,
            'total_monthly_sales': monthly_sales,
            'total_sales': total_sales,
        }

        return render(request, self.template_name, context)

    def get_pdf(self, request, weekly_data, total_weekly_sales, total_orders_this_week, monthly_sales, total_sales):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        content = []
        styles = getSampleStyleSheet()
        title = styles['Title']
        heading = styles['Heading2']

        # Title
        content.append(Paragraph("Weekly Sales Report", title))
        content.append(Spacer(1, 12))

        # Table
        data = [['Day', 'Total Orders', 'Pending Orders', 'Confirmed Orders', 'Total Sales', 'Confirmed Sales', 'Pending Sales']]
        for data_row in weekly_data:
            data.append([
                data_row['day'],
                data_row['total_orders'],
                data_row['pending_orders'],
                data_row['confirmed_orders'],
                f"${data_row['total_sales']:.2f}",
                f"${data_row['confirmed_sales']:.2f}",
                f"${data_row['pending_sales']:.2f}"
            ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(table)

        content.append(Spacer(1, 12))

        # Overall Statistics
        content.append(Paragraph(f"Total Weekly Sales: ${total_weekly_sales:.2f}", heading))
        content.append(Paragraph(f"Total Orders This Week: {total_orders_this_week}", heading))
        content.append(Paragraph(f"Total Monthly Sales: ${monthly_sales:.2f}", heading))
        content.append(Paragraph(f"Total Sales Overall: ${total_sales:.2f}", heading))

        doc.build(content)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="weekly_sales_report.pdf"'
        return response
    
class SalesReportDownloadView(View):
    def get(self, request):
        today = timezone.now()
        start_of_week = today - timezone.timedelta(days=today.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)

        weekly_data = []
        total_weekly_sales = 0
        total_orders_this_week = 0

        for i in range(7):
            day = start_of_week + timezone.timedelta(days=i)
            day_orders = Order.objects.filter(created_at__date=day.date())
            confirmed_orders = day_orders.filter(is_confirmed=True)
            pending_orders = day_orders.filter(is_confirmed=False)

            daily_sales = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            confirmed_sales = confirmed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            pending_sales = pending_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

            weekly_data.append({
                'day': day.strftime('%A'),
                'total_orders': day_orders.count(),
                'pending_orders': pending_orders.count(),
                'confirmed_orders': confirmed_orders.count(),
                'total_sales': daily_sales,
                'confirmed_sales': confirmed_sales,
                'pending_sales': pending_sales
            })

            total_weekly_sales += daily_sales
            total_orders_this_week += day_orders.count()

        # Total Sales for the Month
        start_of_month = today.replace(day=1)
        end_of_month = start_of_month + timezone.timedelta(days=31)  # Assuming a maximum of 31 days in a month
        monthly_sales = Order.objects.filter(created_at__range=[start_of_month, end_of_month]).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Total Sales Overall
        total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        content = []

        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']

        # Title
        title = Paragraph("Weekly Sales Report", title_style)
        content.append(title)
        content.append(Spacer(1, 12))

        # Table
        data = [
            ['Day', 'Total Orders', 'Pending Orders', 'Confirmed Orders', 'Total Sales', 'Confirmed Sales', 'Pending Sales']
        ]
        for row in weekly_data:
            data.append([
                row['day'],
                row['total_orders'],
                row['pending_orders'],
                row['confirmed_orders'],
                f"${row['total_sales']:.2f}",
                f"${row['confirmed_sales']:.2f}",
                f"${row['pending_sales']:.2f}"
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        content.append(table)

        content.append(Spacer(1, 12))

        # Overall Statistics
        stats = [
            f"Total Weekly Sales: ${total_weekly_sales:.2f}",
            f"Total Orders This Week: {total_orders_this_week}",
            f"Total Monthly Sales: ${monthly_sales:.2f}",
            f"Total Sales Overall: ${total_sales:.2f}"
        ]
        for stat in stats:
            content.append(Paragraph(stat, heading_style))
        
        doc.build(content)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="weekly_sales_report.pdf"'
        return response
    
class MonthlySalesReportView(View):
    template_name = 'monthly_sales_report.html'

    def get(self, request):
        today = timezone.now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timezone.timedelta(days=31)).replace(day=1) - timezone.timedelta(days=1)

        daily_data = []
        weekly_data = []
        total_monthly_sales = 0
        total_orders_this_month = 0

        # Get daily data
        for i in range(1, end_of_month.day + 1):
            day = start_of_month.replace(day=i)
            day_orders = Order.objects.filter(created_at__date=day.date())
            daily_sales = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            daily_data.append({
                'day': day.strftime('%d-%b'),
                'total_orders': day_orders.count(),
                'total_sales': daily_sales,
            })

            total_monthly_sales += daily_sales
            total_orders_this_month += day_orders.count()

        # Get weekly data
        start_of_week = start_of_month - timezone.timedelta(days=start_of_month.weekday())
        end_of_week = start_of_week + timezone.timedelta(days=6)

        while start_of_week <= end_of_month:
            week_orders = Order.objects.filter(created_at__range=[start_of_week, end_of_week])
            weekly_sales = week_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
            weekly_data.append({
                'start_date': start_of_week.strftime('%d-%b'),
                'end_date': end_of_week.strftime('%d-%b'),
                'total_orders': week_orders.count(),
                'total_sales': weekly_sales,
            })
            start_of_week += timezone.timedelta(days=7)
            end_of_week += timezone.timedelta(days=7)

        # Generate graphs
        # Daily Sales Line Graph
        days = [data['day'] for data in daily_data]
        daily_sales = [data['total_sales'] for data in daily_data]

        plt.figure(figsize=(10, 5))
        plt.plot(days, daily_sales, marker='o', linestyle='-', color='b')
        plt.title('Daily Sales')
        plt.xlabel('Date')
        plt.ylabel('Total Sales')
        plt.xticks(rotation=45)
        plt.grid(True)
        daily_sales_buf = io.BytesIO()
        plt.savefig(daily_sales_buf, format='png')
        daily_sales_buf.seek(0)
        daily_sales_chart = base64.b64encode(daily_sales_buf.getvalue()).decode('utf-8')
        daily_sales_buf.close()

        # Weekly Sales Bar Chart
        weeks = [f'{week["start_date"]} - {week["end_date"]}' for week in weekly_data]
        weekly_sales = [week['total_sales'] for week in weekly_data]

        plt.figure(figsize=(12, 6))
        plt.bar(weeks, weekly_sales, color='teal')
        plt.title('Weekly Sales')
        plt.xlabel('Week')
        plt.ylabel('Total Sales')
        plt.xticks(rotation=45)
        plt.grid(axis='y')
        bar_chart_buf = io.BytesIO()
        plt.savefig(bar_chart_buf, format='png')
        bar_chart_buf.seek(0)
        bar_chart = base64.b64encode(bar_chart_buf.getvalue()).decode('utf-8')
        bar_chart_buf.close()

        # Weekly Sales Pie Chart
        plt.figure(figsize=(8, 8))
        plt.pie(weekly_sales, labels=weeks, autopct='%1.1f%%', startangle=140)
        plt.title('Weekly Sales Distribution')
        pie_chart_buf = io.BytesIO()
        plt.savefig(pie_chart_buf, format='png')
        pie_chart_buf.seek(0)
        pie_chart = base64.b64encode(pie_chart_buf.getvalue()).decode('utf-8')
        pie_chart_buf.close()

        context = {
            'daily_data': daily_data,
            'weekly_data': weekly_data,
            'total_monthly_sales': total_monthly_sales,
            'total_orders_this_month': total_orders_this_month,
            'daily_sales_chart': daily_sales_chart,
            'bar_chart': bar_chart,
            'pie_chart': pie_chart,
        }

        if 'download' in request.GET:
            return self.generate_pdf_report(request, daily_data, weekly_data, total_monthly_sales, total_orders_this_month, daily_sales_chart, bar_chart, pie_chart)

        return render(request, self.template_name, context)

    def generate_pdf_report(self, request, daily_data, weekly_data, total_monthly_sales, total_orders_this_month, daily_sales_chart, bar_chart, pie_chart):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        pdf.setFont('Helvetica-Bold', 16)
        pdf.drawString(72, height - 72, 'Monthly Sales Report')

        # Summary Statistics
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(72, height - 100, 'Summary Statistics')
        pdf.setFont('Helvetica', 12)
        pdf.drawString(72, height - 120, f'Total Monthly Sales: ${total_monthly_sales}')
        pdf.drawString(72, height - 140, f'Total Orders This Month: {total_orders_this_month}')

        # Daily Sales Data Table
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(72, height - 180, 'Daily Sales Data')
        y_position = height - 200
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(72, y_position, 'Date')
        pdf.drawString(150, y_position, 'Total Orders')
        pdf.drawString(250, y_position, 'Total Sales')
        pdf.setFont('Helvetica', 10)
        y_position -= 20
        for data in daily_data:
            pdf.drawString(72, y_position, data['day'])
            pdf.drawString(150, y_position, str(data['total_orders']))
            pdf.drawString(250, y_position, f'${data["total_sales"]}')
            y_position -= 20

        # Weekly Sales Data Table
        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(72, y_position - 10, 'Weekly Sales Data')
        y_position -= 30
        pdf.setFont('Helvetica-Bold', 10)
        pdf.drawString(72, y_position, 'Week')
        pdf.drawString(150, y_position, 'Total Orders')
        pdf.drawString(250, y_position, 'Total Sales')
        pdf.setFont('Helvetica', 10)
        y_position -= 20
        for week in weekly_data:
            pdf.drawString(72, y_position, f'{week["start_date"]} to {week["end_date"]}')
            pdf.drawString(150, y_position, str(week['total_orders']))
            pdf.drawString(250, y_position, f'${week["total_sales"]}')
            y_position -= 20

        # Save charts to temporary files
        def save_chart_to_file(chart_data, filename):
            file = ContentFile(base64.b64decode(chart_data))
            with default_storage.open(filename, 'wb') as f:
                f.write(file.read())
            return default_storage.url(filename)

        daily_sales_chart_path = 'daily_sales_chart.png'
        bar_chart_path = 'bar_chart.png'
        pie_chart_path = 'pie_chart.png'

        daily_sales_chart_url = save_chart_to_file(daily_sales_chart, daily_sales_chart_path)
        bar_chart_url = save_chart_to_file(bar_chart, bar_chart_path)
        pie_chart_url = save_chart_to_file(pie_chart, pie_chart_path)

        # Add charts to PDF
        pdf.drawImage(daily_sales_chart_url, 72, y_position - 300, width=500, height=300)
        y_position -= 320
        pdf.drawImage(bar_chart_url, 72, y_position - 300, width=500, height=300)
        y_position -= 320
        pdf.drawImage(pie_chart_url, 72, y_position - 300, width=500, height=300)

        pdf.save()
        buffer.seek(0)

        # Clean up temporary files
        default_storage.delete(daily_sales_chart_path)
        default_storage.delete(bar_chart_path)
        default_storage.delete(pie_chart_path)

        return HttpResponse(buffer, as_attachment=True, filename='monthly_sales_report.pdf', content_type='application/pdf')
    

def generate_monthly_report(request):
    today = timezone.now()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timezone.timedelta(days=31)).replace(day=1) - timezone.timedelta(days=1)

    monthly_data = []
    total_monthly_sales = 0
    total_orders_this_month = 0

    for i in range((end_of_month - start_of_month).days + 1):
        day = start_of_month + timezone.timedelta(days=i)
        day_orders = Order.objects.filter(created_at__date=day.date())
        confirmed_orders = day_orders.filter(is_confirmed=True)
        pending_orders = day_orders.filter(is_confirmed=False)

        daily_sales = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        confirmed_sales = confirmed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        pending_sales = pending_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        monthly_data.append({
            'day': day.strftime('%Y-%m-%d'),
            'total_orders': day_orders.count(),
            'pending_orders': pending_orders.count(),
            'confirmed_orders': confirmed_orders.count(),
            'total_sales': daily_sales,
            'confirmed_sales': confirmed_sales,
            'pending_sales': pending_sales
        })

        total_monthly_sales += daily_sales
        total_orders_this_month += day_orders.count()

    # Total Sales Overall
    total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    content = []

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    # Title
    title = Paragraph("Monthly Sales Report", title_style)
    content.append(title)
    content.append(Spacer(1, 12))

    # Table
    data = [
        ['Date', 'Total Orders', 'Pending Orders', 'Confirmed Orders', 'Total Sales', 'Confirmed Sales', 'Pending Sales']
    ]
    for row in monthly_data:
        data.append([
            row['day'],
            row['total_orders'],
            row['pending_orders'],
            row['confirmed_orders'],
            f"${row['total_sales']:.2f}",
            f"${row['confirmed_sales']:.2f}",
            f"${row['pending_sales']:.2f}"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)

    content.append(Spacer(1, 12))

    # Overall Statistics
    stats = [
        f"Total Monthly Sales: ${total_monthly_sales:.2f}",
        f"Total Orders This Month: {total_orders_this_month}",
        f"Total Sales Overall: ${total_sales:.2f}"
    ]
    for stat in stats:
        content.append(Paragraph(stat, heading_style))
    
    doc.build(content)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="monthly_sales_report.pdf"'
    return response