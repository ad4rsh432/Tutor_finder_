from django.urls import path
from .views import home,student_register,tutor_register, dashboard_redirect, student_dashboard,tutor_dashboard,student_profile_view,tutor_profile_view
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from .views import *



urlpatterns = [
    path('',home,name='home'),
    path("register/student/", student_register, name="student_register"),
    path("register/tutor/", tutor_register, name="tutor_register"),
    path("login/", LoginView.as_view(template_name="users/login.html"), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('student/dashboard/', student_dashboard, name='student_dashboard'),
    path('tutor/dashboard/', tutor_dashboard, name='tutor_dashboard'),
    path('profile/student/', student_profile_view, name='student_profile'),
    path('profile/tutor/', tutor_profile_view, name='tutor_profile'),
    path('search-tutors/', search_tutors, name='search_tutors'),
    path('connect/<int:tutor_id>/', send_connection_request, name='send_connection_request'),
    path('approve-request/<int:request_id>/', approve_connection_request, name='approve_connection_request'),
    path('book-session/', book_session_view, name='book_session'),
    path('request-session/<int:tutor_id>/', request_session_view, name='request_session'),
    path('tutor/sessions/', tutor_sessions_view, name='tutor_sessions'),
    path('approve-session/<int:session_id>/', approve_session, name='approve_session'),
    path('session/<int:session_id>/', session_details, name='session_details'),
    path('student_session/', student_sessions_view, name='student_sessions_view'),
    path("tutor/<int:tutor_id>/",view_tutor_profile, name="view_tutor_profile"),
    path("session/<int:session_id>/complete/", mark_session_completed, name="mark_session_completed"),
    path("session/<int:session_id>/rate/", rate_tutor, name="rate_tutor"),
    path('update-location/', update_location, name='update_location'),
    

]
