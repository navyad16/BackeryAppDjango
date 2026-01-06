from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    
    CATEGORY_CHOICES = [
        ('cakes', 'Cakes'),
        ('cookies', 'Cookies'),
        ('bread', 'Bread'),
        ('bisuits','Bisuits'),
        ('pizza','Pizza'),
        ('puff','Puff'),
        ('doughnut','Doughnut'),
        ('muffin','Muffin'),  
        ('somasa','Somasa'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    paid = models.BooleanField(default=False)  # 👈 ADD HERE
    

    STATUS_CHOICES = (
        ('Processing', 'Processing'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Processing'
    )

    # ✅ NEW FIELD
    delivery_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Auto-set delivery date (3 days after order)
        if not self.delivery_date:
            self.delivery_date = timezone.now().date() + timedelta(days=3)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class ProductFeedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="feedbacks")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.user.username}"