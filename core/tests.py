from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import User,Book,Borrow
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date,datetime,timedelta
from unittest.mock import patch
from django.core.mail import send_mail
from django.core import mail


class RegisterAPIViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register-api')  
        self.valid_payload_librarian = {
            "email": "test@gmail.com",
            "password": "test",
            "name": "tester",
            "username": "test",
            "user_type": "librarian"
        }
        self.invalid_payload_without_email = {
            
            "password": "a",
            "name": "surya1",
            "username": "k12"
            
        }
        self.valid_payload_regularuser = {
            "email": "test1@gmail.com",
            "password": "test",
            "name": "tester",
            "username": "test1",
            "user_type": "regular"
        }
        self.invalid_payload_usertype={
             "email": "test@gmail.com",
            "password": "test",
            "name": "tester",
            "username": "test",
            "user_type": "NA"
        }
    
    def test_register_user_with_valid_payload(self):
        response = self.client.post(self.url, self.valid_payload_librarian, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], self.valid_payload_librarian['email'])
        self.assertEqual(response.data['username'], self.valid_payload_librarian['username'])
        self.assertEqual(response.data['user_type'], self.valid_payload_librarian['user_type'])
        self.assertEqual(response.data['name'], self.valid_payload_librarian['name'])
        response = self.client.post(self.url, self.valid_payload_regularuser, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], self.valid_payload_regularuser['email'])
        self.assertEqual(response.data['username'], self.valid_payload_regularuser['username'])
        self.assertEqual(response.data['user_type'], self.valid_payload_regularuser['user_type'])
        self.assertEqual(response.data['name'], self.valid_payload_regularuser['name'])
    
    def test_register_user_with_invalid_payload(self):
        response = self.client.post(self.url, self.invalid_payload_without_email, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(self.url, self.invalid_payload_usertype, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_existing_email(self):      
        User.objects.create_user(
            email=self.valid_payload_librarian['email'],
            password=self.valid_payload_librarian['password'],
            name=self.valid_payload_librarian['name'],
            username=self.valid_payload_librarian['username'],
            user_type=self.valid_payload_librarian['user_type']
        )

       
        response = self.client.post(self.url, self.valid_payload_librarian, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['email'][0], 'user with this email already exists.')

class LoginAPIViewTestCase(TestCase):
    def setUp(self):
        self.client=APIClient()
        self.url=reverse("login-api")
        self.valid_payload_librarian={
            "email": "test@gmail.com",
            "password": "tster",
            "name": "tester",
            "username": "test"
        }
        self.valid_login_credential_payload={
            "email":"test@gmail.com",
            "password":"tster"
        }  
        self.invalid_credentials={
             "email":"test@gmail.com",
            "password":"tster1"
        }
    def test_register_user_correct_credentials(self):
        User.objects.create_user(email=self.valid_payload_librarian['email'],
            password=self.valid_payload_librarian['password'],
            name=self.valid_payload_librarian['name'],
            username=self.valid_payload_librarian['username'])
        
        response=self.client.post(self.url,self.valid_login_credential_payload,format="json")
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)

    def test_register_user_email_doesnt_exist(self):
        response=self.client.post(self.url,self.valid_login_credential_payload,format="json")
        self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)


    def test_register_wrong_credentials(self):
        User.objects.create_user(email=self.valid_payload_librarian['email'],
            password=self.valid_payload_librarian['password'],
            name=self.valid_payload_librarian['name'],
            username=self.valid_payload_librarian['username'])
        
        response=self.client.post(self.url,self.invalid_credentials,format="json")
        self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
        
class GetUserAPIViewTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian'  
        )
        self.url = reverse('getuser-api')  

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_user_with_valid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['name'], self.user.name)
        self.assertEqual(response.data['user_type'], self.user.user_type)


    def test_get_user_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + 'invalidtoken')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class DeleteUserAPIViewTestCase(TestCase): 
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian'  
        )
        self.invaliduser = {
            'email':'testuser1@example.com',
            'password':'testpassword',
            'name':'Test User',
            'username':'testuser',
            'user_type':'librarian' 
        }
        self.url = reverse('deleteuser-api') 

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_delete_valid_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class UpdateUserAPIViewTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian'   
        )
        self.payload_user_update = {
            "email": "test33333@gmail.com",
            "password": "test",
            "name": "tester",
            "username": "test333333"
        }
        self.url = reverse('updateuser-api')  

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_update_valid_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.put(self.url, self.payload_user_update, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['email'], self.payload_user_update['email'])
        self.assertEqual(response.data['name'], self.payload_user_update['name'])
        self.assertEqual(response.data['username'], self.payload_user_update['username'])
    
class GetBooksTestCase(TestCase):

    def setUp(self):
        self.url = reverse("getbooks-api")
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian' 
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.books = [
            Book.objects.create(
                title=f'Example Book{i}',
                author=f'John Doe{i}',
                published_date=date(2024, 11, 13),
                quantity=i * 10
            ) for i in range(15)
        ]

    def test_valid_user_get_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  
      

        first_book = response.data[0]
        self.assertIn('id', first_book)
        self.assertIn('title', first_book)
        self.assertIn('author', first_book)
        self.assertIn('published_date', first_book)
        self.assertIn('quantity', first_book)

    def test_wrong_authentication_get_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token+"!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DeleteBooksTestCase(TestCase):

    def setUp(self):
        self.user_librarian = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian'
        )
        self.user_regular = User.objects.create_user(
            email='testuser1@example.com',
            password='testpassword',
            name='Test User',
            username='testuser1',
            user_type='regular'
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user_librarian)
        self.access_token_librarian = str(refresh.access_token)

        refresh = RefreshToken.for_user(self.user_regular)
        self.access_token_regular = str(refresh.access_token)

        self.book = Book.objects.create(
            title='Example Book deleted',
            author='TBD',
            published_date=date(2024, 11, 13),
            quantity=10
        )

        self.url = reverse("deletebook-api", args=[self.book.id])
        self.wrong_url=reverse("deletebook-api", args=[self.book.id+1])
    def test_valid_user_delete_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_librarian)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_regular_user_delete_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_bookid_user_delete_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_librarian)
        response = self.client.delete(self.wrong_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class UpdateBookTestCase(TestCase):
    pass 
    def setUp(self):
        self.user_librarian = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian'
        )
        self.user_regular = User.objects.create_user(
            email='testuser1@example.com',
            password='testpassword',
            name='Test User',
            username='testuser1',
            user_type='regular'
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user_librarian)
        self.access_token_librarian = str(refresh.access_token)

        refresh = RefreshToken.for_user(self.user_regular)
        self.access_token_regular = str(refresh.access_token)

        self.book = Book.objects.create(
            title='Example Book deleted',
            author='TBD',
            published_date=date(2024, 11, 13),
            quantity=10
        )
        self.book_update={
        
        "title": "Updated title",
        "author": "updated author",
        "published_date": "2024-11-13",
        "quantity": 100
    }
        
        self.url = reverse("updatebook-api", args=[self.book.id])
        self.wrong_url=reverse("updatebook-api", args=[self.book.id+1])

    def test_valid_user_update_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_librarian)
        response = self.client.put(self.url,self.book_update)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["title"], self.book_update["title"])
        self.assertEqual(response.data["author"], self.book_update["author"])
        self.assertEqual(response.data["published_date"], self.book_update["published_date"])
        self.assertEqual(response.data["quantity"], self.book_update["quantity"])

    def test_regular_user_update_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response = self.client.put(self.url,self.book_update)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_bookid_user_delete_books(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_librarian)
        response = self.client.put(self.wrong_url,self.book_update)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
        
class BorrowAPITestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            name='Test User',
            email='testuser@example.com',
            password='testpassword',
            username='testuser',
            user_type='regular'
        )
        
        self.librarian = User.objects.create_user(
            name='Librarian User',
            email='librarian@example.com',
            password='librarianpassword',
            username='librarianuser',
            user_type='librarian'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            published_date=datetime.now().date(),
            quantity=5
        )
        
        self.url = reverse('borrow-book-api', args=[self.book.id])
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token_regular = str(refresh.access_token)

    def test_borrow_book_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        borrow_record = Borrow.objects.filter(user=self.user, book=self.book).first()
        self.assertIsNotNone(borrow_record)
        
        self.book.refresh_from_db()
        
        self.assertEqual(self.book.quantity, 4)
        
class BorrowAPITestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            name='Test User',
            email='testuser@example.com',
            password='testpassword',
            username='testuser',
            user_type='regular'
        )
        
        self.librarian = User.objects.create_user(
            name='Librarian User',
            email='librarian@example.com',
            password='librarianpassword',
            username='librarianuser',
            user_type='librarian'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            published_date=datetime.now().date(),
            quantity=5
        )
        
        self.url = reverse('borrow-book-api', args=[self.book.id])
        
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token_regular = str(refresh.access_token)

    def test_borrow_book_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response = self.client.get(self.url)
        
       
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        borrow_record = Borrow.objects.filter(user=self.user, book=self.book).first()
        self.assertIsNotNone(borrow_record)
        
        self.book.refresh_from_db()
        
        self.assertEqual(self.book.quantity, 4)

    def test_borrow_book_not_available(self):
        self.book.quantity = 0
        self.book.save()
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response = self.client.get(self.url)
        self.assertEqual(response.data['message'], 'Book is not available at the moment')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        self.assertEqual(Borrow.objects.count(), 0)

    def test_borrow_book_invalid_id(self):
        invalid_url = reverse('borrow-book-api', args=[999])
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response = self.client.get(invalid_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        self.assertEqual(response.data['error'], 'The book ID doesnt exist')
        
        self.assertEqual(Borrow.objects.count(), 0)

        
class ReturnAPITestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            name='Test User',
            email='testuser@example.com',
            password='testpassword',
            username='testuser',
            user_type='regular'
        )
        
        self.librarian = User.objects.create_user(
            name='Librarian User',
            email='librarian@example.com',
            password='librarianpassword',
            username='librarianuser',
            user_type='librarian'
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            published_date=datetime.now().date(),
            quantity=5
        )
        
        self.url = reverse('borrow-book-api', args=[self.book.id])
        self.book_return=reverse("bookreturn-api",args=[self.book.id])
        self.book_return_invalid=reverse("bookreturn-api",args=[self.book.id+1])
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.access_token_regular = str(refresh.access_token)

    def test_borrow_book_success(self):
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
            response = self.client.get(self.url)
            
        
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            borrow_record = Borrow.objects.filter(user=self.user, book=self.book).first()
            self.assertIsNotNone(borrow_record)
            
            self.book.refresh_from_db()
            
            
            self.assertEqual(self.book.quantity, 4)

            response_return=self.client.post(self.book_return)
            self.assertEqual(response_return.status_code, status.HTTP_200_OK)
            borrow_record = Borrow.objects.filter(user=self.user, book=self.book).first()
            
            self.book.refresh_from_db()
            self.assertEqual(self.book.quantity, 5)

    def test_borrow_book_nonborrowed(self):
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            borrow_record = Borrow.objects.filter(user=self.user, book=self.book).first()
            self.assertIsNotNone(borrow_record)
            
            self.book.refresh_from_db()
            
            
            self.assertEqual(self.book.quantity, 4)

            response_return=self.client.post(self.book_return_invalid)
            self.assertEqual(response_return.status_code, status.HTTP_404_NOT_FOUND)

class OverDueUsersViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='suryaramdevi@gmail.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian'  
        )
        
        self.book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            published_date=datetime.now().date(),
            quantity=5
        )
        
        self.borrow_record = Borrow.objects.create(
            user=self.user,
            book=self.book,
            start_date=datetime.now().date() - timedelta(days=20),  
            end_date=datetime.now().date() - timedelta(days=10), 
            returned_date=None
        )

        self.client = APIClient()
        self.url = reverse('overdue-sendemail-api')
        refresh = RefreshToken.for_user(self.user)
        self.access_token_regular = str(refresh.access_token)

    
    def test_overdue_email(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token_regular)
        response=self.client.post(self.url)
        print(response.data)        

        self.assertEqual(response.status_code, 200)
        self.assertIn('email sent to the below users', response.data['message'])

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Book return is overdue')
        self.assertEqual(mail.outbox[0].to, ['suryaramdevi@gmail.com'])
        self.assertIn('Dear Test User', mail.outbox[0].body)
        self.assertIn('We hope you enjoyed reading the book, but you havent returned the book yet.', mail.outbox[0].body)
        

class SearchBookAPIViewTest(TestCase):


    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='regular' 
        )

        self.book1 = Book.objects.create(
            title='Django for Beginners',
            author='William S. Vincent',
            published_date='2020-01-01',
            quantity=5
        )
        self.book2 = Book.objects.create(
            title='Two Scoops of Django',
            author='Daniel Roy Greenfeld',
            published_date='2019-01-01',
            quantity=3
        )
        self.book3 = Book.objects.create(
            title='Learning Python',
            author='Mark Lutz',
            published_date='2018-01-01',
            quantity=2
        )

        self.client = APIClient()
        self.url = reverse('book-search-api') 
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_search_by_title(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url, {'query': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2) 
        self.assertEqual(response.data[0]['title'], 'Django for Beginners')
        self.assertEqual(response.data[1]['title'], 'Two Scoops of Django')

    def test_search_by_author(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url, {'query': 'Mark Lutz'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Learning Python')

    def test_search_no_query(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)  

class FilterBorrowedBooksAPIViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword',
            name='Test User',
            username='testuser',
            user_type='librarian' 
        )

        self.user2 = User.objects.create_user(
            email='testuser2@example.com',
            password='testpassword2',
            name='Test User 2',
            username='testuser2',
            user_type='regular'
        )

        self.book1 = Book.objects.create(
            title='Django for Beginners',
            author='William S. Vincent',
            published_date='2020-01-01',
            quantity=5
        )
        self.book2 = Book.objects.create(
            title='Two Scoops of Django',
            author='Daniel Roy Greenfeld',
            published_date='2019-01-01',
            quantity=3
        )

       
        self.borrow1 = Borrow.objects.create(
            user=self.user,
            book=self.book1,
            start_date=datetime.now().date() - timedelta(days=10),
            end_date=datetime.now().date() - timedelta(days=5)
        )
        self.borrow2 = Borrow.objects.create(
            user=self.user2,
            book=self.book2,
            start_date=datetime.now().date() - timedelta(days=20),
            end_date=datetime.now().date() - timedelta(days=15)
        )

        self.client = APIClient()
        self.url = reverse('filter-borrowed-books-api') 
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_filter_by_user_id(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url, {'user_id': self.user.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user.id)

    def test_filter_by_start_date(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url, {'start_date': (datetime.now().date() - timedelta(days=15)).isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['start_date'], self.borrow1.start_date.isoformat())

    def test_filter_by_end_date(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url, {'end_date': (datetime.now().date() - timedelta(days=10)).isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['end_date'], self.borrow2.end_date.isoformat())

    def test_filter_by_user_id_and_dates(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url, {
            'user_id': self.user.id,
            'start_date': (datetime.now().date() - timedelta(days=15)).isoformat(),
            'end_date': (datetime.now().date() - timedelta(days=5)).isoformat()
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user.id)
        self.assertEqual(response.data[0]['start_date'], self.borrow1.start_date.isoformat())
        self.assertEqual(response.data[0]['end_date'], self.borrow1.end_date.isoformat())

    def test_no_filters(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

