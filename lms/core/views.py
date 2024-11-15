import datetime
from rest_framework.authentication import get_authorization_header
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status
from .authentication import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token
from .serializers import BorrowSerializer, UserSerializer,BookSerializer
from .models import User,Book,Borrow
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q



class RegisterAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        user = User.objects.filter(email=request.data['email']).first()

        if not user:
            raise APIException('Invalid credentials!')

        if not user.check_password(request.data['password']):
            raise APIException('Invalid credentials!')

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        response = Response()

        response.set_cookie(key='refreshToken', value=refresh_token, httponly=True)
        response.data = {
            'token': access_token
        }

        return response


class UserAPIView(APIView):
    
    def get(self, request):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            user = User.objects.filter(pk=id).first()

            return Response(UserSerializer(user).data)

        raise AuthenticationFailed('unauthenticated')

    def put(self, request):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            user = User.objects.filter(pk=id).first()
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=400)

        raise AuthenticationFailed('unauthenticated')

    def delete(self, request):
        auth = get_authorization_header(request).split()

        if auth and len(auth) == 2:
            token = auth[1].decode('utf-8')
            id = decode_access_token(token)

            user = User.objects.filter(pk=id).first()
            if user:
                user.delete()
                return Response(status=204)

        raise AuthenticationFailed('unauthenticated')


class RefreshAPIView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('refreshToken')
        id = decode_refresh_token(refresh_token)
        access_token = create_access_token(id)
        return Response({
            'token': access_token
        })


class LogoutAPIView(APIView):
    def post(self, _):
        response = Response()
        response.delete_cookie(key="refreshToken")
        response.data = {
            'message': 'success'
        }
        return response
    

class BookAPIView(APIView):
    def post(self, request):
        print("Request data:", request.data)  # Debug statement
        bookserializer = BookSerializer(data=request.data)
        if bookserializer.is_valid():
            print("Validated data:", bookserializer.validated_data)  # Debug statement
            bookserializer.save()
            return Response(bookserializer.data, status=status.HTTP_201_CREATED)
        print("Errors:", bookserializer.errors)  # Debug statement
        return Response(bookserializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        list_books = Book.objects.all()
        try:
            page=request.GET.get("page",1)
            page_size=3
            paginator=Paginator(list_books,page_size)
            print(paginator.page(page))
            bookserializer = BookSerializer(paginator.page(page), many=True)
        except Exception as e:
            return Response({"message":"Out of bounds"},status=status.HTTP_404_NOT_FOUND)

        return Response(bookserializer.data)
    
     
        
    
class BookDeleteAPIView(APIView):
    def delete(self,request,bookid):
        pass 
        book_to_delete=Book.objects.get(id=bookid)
        if book_to_delete is not None:
            book_to_delete.delete()
        else:
            raise APIException("book Not found")
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class UpdateBookAPIView(APIView):
    def put(self,request,bookid):
         
        book_to_update=Book.objects.get(id=bookid)
        if book_to_update is not None:
            pass
            bookserializer=BookSerializer(book_to_update,data=request.data,partial=True)
            if bookserializer.is_valid():
                bookserializer.save()
        else:
            raise APIException("Book Not found")
        return Response(bookserializer.data)    
        
class BorrowAPIView(APIView):

    def get(self,request,bookid):
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
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            
            return Response({"message":"error"})
        else:
            return Response({"message":"NA"})
        


class ReturnBookView(APIView):  
    def post(self,request,book_id):
        try:
            print("QSSSS ",book_id)
            auth = get_authorization_header(request).split()
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

            # Increase the quantity of the book
            print("CNT ",count)
            book = Book.objects.get(id=book_id)
            # book.quantity += borrow_records.count()
            book.quantity +=count
            book.save()
        except Borrow.DoesNotExist:
            return Response({'error': 'No active borrow record found for this book and user'}, status=status.HTTP_404_NOT_FOUND)

        # Update the returned_date to the current date
        borrow_record.returned_date = datetime.datetime.now().date()
        borrow_record.save()

       

        return Response({'message': 'Book returned successfully'}, status=status.HTTP_200_OK)
                
class OverDueUsersView(APIView):
    def post(self,request):
        today = datetime.datetime.now().date()
        borrow_records = Borrow.objects.filter(returned_date__isnull=True, end_date__lt=today)
        users=[]
        for record in borrow_records:
            print("rec ",record)
            users.append(record.user)

        for user in users:
            print("USEDD",user.email,user.name)
            send_mail(
                'Book return is overdue',
                f'Dear {user.name},\n\n We hope you enjoyed reading the book, but you havent returned the book yet.Could you please return the book ASAP.\n\nBest regards,\nLibrary Team',
                'akshayak12300@gmail.com',
                [user.email],
                fail_silently=False,
            )


        return Response({"email":"!@#"})

        #user_ids = [record['user_id'] for record in borrow_records]

class SearchBookAPIView(APIView):
    # def get(self,request):
    #     title=request.GET.get("title",None)
    #     author=request.GET.get("author",None)
    #     if title and author:
    #         books = Book.objects.filter(Q(title__icontains=title) | Q(author__icontains=author))

    #     elif title:
    #         books = Book.objects.filter(title__icontains=title)
    #     elif author:
    #         books = Book.objects.filter(author__icontains=author)
    #     else:
    #         books = Book.objects.all()

    #     serializer = BookSerializer(books, many=True)
    #     return Response(serializer.data)        
    def get(self,request):
        query = request.GET.get('query', '')
        print("QQQQQ ",query)
        if query:
            # Search by title or author, case insensitive
            books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
        else:
            books = Book.objects.all()  # Optionally return all books if no query
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

class FilterBorrowedBooksAPIView(APIView):
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
        