# models.py (bookstore)

from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    published_date = models.DateField()
    categories = models.ManyToManyField(Category)
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)
    default_rating = models.FloatField(default=2.5)

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"
    
    @property
    def total_amount(self):
        return sum(Book.total for book in self.Book.all)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart,related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.book.title} in cart"

    @property
    def book_price(self):
        return self.book.price

    @property
    def book_category(self):
        # Assuming each book has only one category for simplicity
        return self.book.categories.first().name
    


class Order(models.Model):


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    address_line1 = models.CharField(max_length=255, null=True, default=None, blank=True  )
    address_line2 = models.CharField(max_length=255, blank=True, null=True,default=None)
    city = models.CharField(max_length=100,null=True, default=None, blank=True)
    state = models.CharField(max_length=100,null=True, default=None, blank=True)
    zip_code = models.CharField(max_length=20, default = 411033)
    is_confirmed = models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)





class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)  # Assuming Book model exists
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.quantity * self.price
    

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=2.5)
    review = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')


class Review(models.Model):
    product = models.ForeignKey(Book, related_name='reviews', on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f'Review for {self.product.name} by {self.customer.username}'

    class Meta:
        ordering = ['-created_at']
  
