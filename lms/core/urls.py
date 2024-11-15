from django.urls import path
from .views import RegisterAPIView, LoginAPIView, UserAPIView, RefreshAPIView, LogoutAPIView,BookAPIView,BookDeleteAPIView,UpdateBookAPIView,BorrowAPIView,ReturnBookView,OverDueUsersView,SearchBookAPIView,FilterBorrowedBooksAPIView

urlpatterns = [
    path('register', RegisterAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    path('user', UserAPIView.as_view()),
    path('refresh', RefreshAPIView.as_view()),
    path('logout', LogoutAPIView.as_view()),
     path('books', BookAPIView.as_view()),
     path('deletebook/<int:bookid>', BookDeleteAPIView.as_view()),
     path('updatebook/<int:bookid>', UpdateBookAPIView.as_view()),
     path('borrowbook/<int:bookid>', BorrowAPIView.as_view()),
     path('bookreturn/<int:book_id>', ReturnBookView.as_view()),
     path('overdue/sendemail', OverDueUsersView.as_view()),
     path("books/search",SearchBookAPIView.as_view()),
     path("listborrowedbooks",FilterBorrowedBooksAPIView.as_view())
]