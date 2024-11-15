from django.urls import path

from core import views
urlpatterns = [
    path('register', views.RegisterAPIView.as_view(),name="register-api"),
    path('login', views.LoginAPIView.as_view(),name="login-api"),
    path('getuser', views.GetUserAPIView.as_view(),name="getuser-api"),
    path("deleteuser",views.DeleteUserAPIView.as_view(),name="deleteuser-api"),
    path("updateuser",views.UpdateUserAPIView.as_view(),name="updateuser-api"),
    path('refreshtoken', views.RefreshAPIView.as_view()),
    path('logout', views.LogoutAPIView.as_view()),

     
     path('getbooks', views.BookAPIView.as_view(),name="getbooks-api"),
     path('addbook', views.AddBookAPIView.as_view(),name="addbooks-api"),
     path('deletebook/<int:bookid>', views.BookDeleteAPIView.as_view(),name="deletebook-api"),
     path('updatebook/<int:bookid>', views.UpdateBookAPIView.as_view(),name="updatebook-api"),
     path('borrowbook/<int:bookid>', views.BorrowAPIView.as_view(),name="borrow-book-api"),
     path('bookreturn/<int:book_id>',views.ReturnBookView.as_view(),name="bookreturn-api"),

     path('overdue/sendemail', views.OverDueUsersView.as_view(),name="overdue-sendemail-api"),
     path("books/search",views.SearchBookAPIView.as_view(),name="book-search-api"),
     path("listborrowedbooks",views.FilterBorrowedBooksAPIView.as_view(),name="filter-borrowed-books-api"),
     path('add/review/<int:bookid>', views.AddReviewView.as_view(), name='addreview'),
    path('books/<int:bookid>/reviews', views.ListReviewsView.as_view(), name='list-reviews'),
    path('books/<int:bookid>/average-rating', views.AverageRatingView.as_view(), name='average-rating'),
]