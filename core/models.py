from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    USER_TYPE_CHOICES=(("librarian","Librarian"),
                       ("regular","Regular"))
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=150, unique=True)  # Add username field
    user_type=models.CharField(max_length=15,choices=USER_TYPE_CHOICES,default="regular")

    first_name = None
    last_name = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Add username to required fields

    def __str__(self):
        return self.email
    
    def is_librarian(self):
        return self.user_type=="librarian"
    
    def is_regular_user(self):
        return self.user_type=="regular"
    
class Book(models.Model):

    title=models.CharField(max_length=500)
    author=models.CharField(max_length=500)
    published_date=models.DateField()
    quantity=models.IntegerField()

    def __str__(self):
        return f'Book:{self.title}, quantity:{self.quantity}'
    

class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    returned_date=models.DateField(null=True,blank=True)

    def __str__(self):
        return f'{self.user.email} borrowed {self.book.title} from {self.start_date} to {self.end_date} returned {self.returned_date}'
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Review by {self.user.email} for {self.book.title}'