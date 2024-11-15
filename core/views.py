import datetime
from rest_framework.authentication import get_authorization_header
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status
from .authentication import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from .serializers import BorrowSerializer, ReviewSerializer, UserSerializer,BookSerializer
from .models import User,Book,Borrow,Review
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from .permissions import IsLibrarian, IsRegularUser
from django.db.models import Avg
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

"""
Registers the user with username,email,password,name and regular as default user_type if not given in payload for both librarian and regular user
"""
class RegisterAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

"""
Function returns a access token that is valid for 1 day and sets a refresh token as a cookie that is valid for 7 days for both librarian and regular user
"""
class LoginAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):    
        user = User.objects.filter(email=request.data['email']).first()
        if not user:
            return Response({"error":"User with the email doesnt exist"},status=status.HTTP_404_NOT_FOUND)
             

        if not user.check_password(request.data['password']):
            return Response({"error":"Invalid credentials"},status=status.HTTP_401_UNAUTHORIZED)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        response = Response(status=status.HTTP_201_CREATED)

        response.set_cookie(key='refreshToken', value=refresh_token, httponly=True)
        response.data = {
            'token': access_token
        }

        return response

"""
API that returns the profile of the current user except the password for both librarian and regular user
"""
class GetUserAPIView(APIView):
    permission_classes=[IsAuthenticated, IsLibrarian| IsRegularUser]
    def get(self, request):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            user = User.objects.filter(pk=id).first()

            return Response(UserSerializer(user).data)

        raise AuthenticationFailed('unauthenticated')


"""
Deletes the current user's profile for both librarian and regular user
"""
class DeleteUserAPIView(APIView):
    permission_classes=[IsAuthenticated, IsLibrarian| IsRegularUser]
    def delete(self, request):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            user = User.objects.filter(pk=id).first()
            if user:
                user.delete()
                return Response({"message":"successfully deleted"},status=204)

        return Response(status=status.HTTP_404_NOT_FOUND)
    

"""
Updates the current user's profile with partial and full update for both librarian and regular user
"""
class UpdateUserAPIView(APIView):

    def put(self, request):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            user = User.objects.filter(pk=id).first()
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_202_ACCEPTED)
            return Response(serializer.errors, status=400)

        raise AuthenticationFailed('unauthenticated')

   
    

"""
Api that fetches the cookie refresh token and generates a new access token and sends it as a response for both librarian and regular user
"""
class RefreshAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        print("Inside here")
        refresh_token = request.COOKIES.get('refreshToken')
        id = decode_refresh_token(refresh_token)
        access_token = create_access_token(id)
        return Response({
            'token': access_token
        })

"""
Logs the user out by deleting the refreshtoken  for both librarian and regular user
"""
class LogoutAPIView(APIView):
    # permission_classes=[IsAuthenticated]
    # def post(self, request):
    #     auth = get_authorization_header(request).split()
    #     response = Response()
    #     response.delete_cookie(key="refreshToken")
        
    #     response.data = {
    #         'message': 'success'
    #     }
    #     return response
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
            print(f"Refresh token from cookie: {refresh_token}")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                print("Token blacklisted successfully")
            else:
                print("Refresh token not found in cookies")
                return Response({"error": "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)
            response = Response(status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
            response.data = {
                'message': 'success'
            }
            return response
        except Exception as e:
            print(f"Error during logout: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
"""
gets all  the books   for both librarian and regular user
"""
class BookAPIView(APIView):
    
    permission_classes=[IsAuthenticated,IsLibrarian|IsRegularUser]
    

    def get(self, request):
        list_books = Book.objects.all()
        try:
            page=request.GET.get("page",1)
            page_size=3
            paginator=Paginator(list_books,page_size)
            print(paginator.page(page))
            bookserializer = BookSerializer(paginator.page(page), many=True)
        except Exception as e:
            return Response({"message":"Out of bounds"},status=status.HTTP_401_UNAUTHORIZED)

        return Response(bookserializer.data,status=status.HTTP_200_OK)
    
class AddBookAPIView(APIView):
    permission_classes = [IsAuthenticated, IsLibrarian]

    def post(self, request):
        bookserializer = BookSerializer(data=request.data)
        if bookserializer.is_valid():
            bookserializer.save()
            return Response(bookserializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(bookserializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
"""
Deletes the book with the bookid only for librarian
"""
class BookDeleteAPIView(APIView):
    permission_classes=[IsAuthenticated,IsLibrarian]
    def delete(self,request,bookid):
        pass 
        if Book.objects.filter(id=bookid).exists():
            print("BBBBBB ",bookid)
            book_to_delete=Book.objects.get(id=bookid)
            print("BBBB ",book_to_delete)
            if book_to_delete is not None:
                book_to_delete.delete()
                return Response({"message":"deleted successfully"},status=status.HTTP_204_NO_CONTENT)
            else:
                raise APIException("book Not found")
            
        else:
            return Response({"error":"The book ID doesnt exist"},status=status.HTTP_404_NOT_FOUND)
    
"""
updates the details of the book,partial update is also possible, only for librarian
"""
class UpdateBookAPIView(APIView):
    permission_classes=[IsAuthenticated,IsLibrarian]
    def put(self,request,bookid):
         
        if Book.objects.filter(id=bookid).exists():
            book_to_update=Book.objects.get(id=bookid)
            if book_to_update is not None:
                pass
                bookserializer=BookSerializer(book_to_update,data=request.data,partial=True)
                if bookserializer.is_valid():
                    bookserializer.save()
            else:
                return Response({"error":"The book ID doesnt exist"},status=status.HTTP_404_NOT_FOUND)
            return Response(bookserializer.data,status=status.HTTP_202_ACCEPTED)    
        else:
            return Response({"error":"The book ID doesnt exist"},status=status.HTTP_404_NOT_FOUND)
        
"""
borrow book for a particular user for a particular bookid and only for regular user
"""
class BorrowAPIView(APIView):
    permission_classes=[IsAuthenticated,IsRegularUser]
    def get(self,request,bookid):
        if Book.objects.filter(id=bookid).exists():
            book = Book.objects.get(id=bookid)
            auth = get_authorization_header(request).split()
            if auth and len(auth) == 2:
                token = auth[1].decode('utf-8')
                id = decode_access_token(token)

                user = User.objects.filter(pk=id).first()
            print("AAA->",user,book)
            
            
            if book.quantity > 0:
                start_date = datetime.datetime.now().date()
                end_date = start_date + datetime.timedelta(days=14)  
                borrow_data = {
                    'user': user.id,
                    'book': book.id,
                    'start_date': start_date,
                    'end_date': end_date,
                    "returned_date": None
                }
                print("borrowwwww ",borrow_data)
                serializer = BorrowSerializer(data=borrow_data)
                
                serializer = BorrowSerializer(data=borrow_data)
                if serializer.is_valid():
                    serializer.save()
                    book.quantity -= 1
                    book.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                
                
                return Response({"message":serializer.errors},status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"message":"Book is not available at the moment"},status=status.HTTP_404_NOT_FOUND)
        
        else:
            return Response({"error":"The book ID doesnt exist"},status=status.HTTP_404_NOT_FOUND)

"""
User returns the borrowed book with bookid only for regular user

"""
class ReturnBookView(APIView):  
    permission_classes=[IsAuthenticated,IsRegularUser]
    def post(self,request,book_id):
        try:
            print("QSSSS ",book_id)
            auth = get_authorization_header(request).split()
            token = auth[1].decode('utf-8')
            if auth and len(auth) == 2:
                print("QSSS1S ",book_id,auth)
                token = auth[1].decode('utf-8')
                id = decode_access_token(token)
                print("QSSS1S2 ",id)
                user = User.objects.filter(pk=id).first()
                
                print("QSSSS ",id,book_id)
            borrow_records = Borrow.objects.filter(book_id=book_id, user_id=id, returned_date__isnull=True)
            if not borrow_records.exists():
                 return Response({'error': 'No active borrow record found for this book and user'}, status=status.HTTP_404_NOT_FOUND)
            count=0
            for borrow_record in borrow_records:
                print("rec->>> ",borrow_record.user.id,borrow_record.user.email)
                borrow_record.returned_date = datetime.datetime.now().date()
                borrow_record.save()
                count+=1

            print("CNT ",count)
            book = Book.objects.get(id=book_id)
            # book.quantity += borrow_records.count()
            book.quantity +=count
            book.save()
            Response({"message":"books returned successfully"},status=status.HTTP_200_OK)
        except Borrow.DoesNotExist:
            return Response({'error': 'No active borrow record found for this book and user'}, status=status.HTTP_404_NOT_FOUND)

        borrow_record.returned_date = datetime.datetime.now().date()
        borrow_record.save()

       

        return Response({'message': 'Book returned successfully'}, status=status.HTTP_200_OK)

"""
sends out an email for all the overdue customers who havent returned their book yet only for librarian
"""
class OverDueUsersView(APIView):
    permission_classes = [IsAuthenticated,IsLibrarian]
    print("is it workinggggggggg")
    def post(self, request):
        print("is it workinggggggggg2")
        today = datetime.datetime.now().date()
        borrow_records = Borrow.objects.filter(returned_date__isnull=True, end_date__lt=today)
        print("bb record",borrow_records)
        users = []

        for record in borrow_records:
            users.append(record.user)

        for user in users:
            print("user  ",user.name,user.email)
            t=send_mail(
                'Book return is overdue',
                f'Dear {user.name},\n\n We hope you enjoyed reading the book, but you havent returned the book yet.Could you please return the book ASAP.\n\nBest regards,\nLibrary Team',
                'akshayak12300@gmail.com',
                [user.email],
                fail_silently=False,
            )
            print(t)

        return Response({"message": "email sent to the below users", "users": [user.email for user in users]}, status=status.HTTP_200_OK)

"""
search for books using query from the api and returns possible matches for both librarian and regular user
"""
class SearchBookAPIView(APIView):

    permission_classes=[IsAuthenticated,IsRegularUser|IsLibrarian]  
    def get(self,request):
        query = request.GET.get('query', '')
        print("QQQQQ ",query)
        if query:
            books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
        else:
            books = Book.objects.all() 
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

"""
filters borrowed books only for librarian
"""
class FilterBorrowedBooksAPIView(APIView):
    permission_classes=[IsAuthenticated,IsLibrarian]
    def get(self,request):
        user_id = request.GET.get('user_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        filters = Q()
        if user_id:
            filters &= Q(user__id=user_id)
        if start_date:
            filters &= Q(start_date__gte=start_date)
        if end_date:
            filters &= Q(end_date__lte=end_date)

        borrowed_books = Borrow.objects.filter(filters)
        serializer = BorrowSerializer(borrowed_books, many=True)
        return Response(serializer.data)
        
"""
Add review for a particular bookid from a particular user only for regular user
"""
class AddReviewView(APIView):
    permission_classes = [IsAuthenticated,IsRegularUser]

    def post(self, request, bookid):
        try:
            book = Book.objects.get(id=bookid)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already reviewed this book
        if Review.objects.filter(user=request.user, book=book).exists():
            return Response({"error": "You have already reviewed this book"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, book=book)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

"""
list out all the reviews applicable for both regular and librarian user
"""
class ListReviewsView(APIView):
    permission_classes = [IsAuthenticated,IsRegularUser|IsLibrarian]
    def get(self, request, bookid):
        reviews = Review.objects.filter(book__id=bookid)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
"""
Gives out average rating for a particular book 
"""
class AverageRatingView(APIView):

    permission_classes = [IsAuthenticated,IsRegularUser|IsLibrarian]
    def get(self, request, bookid):
        book = Book.objects.get(id=bookid)
        average_rating = Review.objects.filter(book=book).aggregate(Avg('rating'))['rating__avg']
        data = {
            'id': book.id,
            'title': book.title,
            'average_rating': average_rating
        }
        return Response(data)
    def get(self, request, bookid):
        book = Book.objects.get(id=bookid)
        average_rating = Review.objects.filter(book=book).aggregate(Avg('rating'))['rating__avg']
        data = {
            'id': book.id,
            'title': book.title,
            'average_rating': average_rating
        }
        return Response(data)
    

def logout_common(token):
            try:
                refresh_token = token
                print(f"Refresh token from cookie: {refresh_token}")
                if refresh_token:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    print("Token blacklisted successfully")
                else:
                    print("Refresh token not found in cookies")
                    return Response({"error": "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)
                response = Response(status=status.HTTP_205_RESET_CONTENT)
                response.delete_cookie(settings.SIMPLE_JWT['AUTH_COOKIE'])
                response.data = {
                    'message': 'success'
                }
                return response
            except Exception as e:
                print(f"Error during logout: {e}")
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
  