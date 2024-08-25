from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
urlpatterns = [
    path('home/', views.home, name='home'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('submit-clearance/', views.submit_clearance, name='submit_clearance'),
    path('view-clearance/', views.view_clearance, name='view_clearance'),
    path('staff-home/', views.staff_home, name='staff_home'),
    path('process-clearance/<int:section_id>/', views.process_clearance, name='process_clearance'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('upload-document/<int:section_id>/', views.upload_document, name='upload_document'),
    path('verify-document/<int:document_id>/', views.verify_document, name='verify_document'),

]
