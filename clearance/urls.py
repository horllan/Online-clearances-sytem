from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('submit-clearance/', views.submit_clearance, name='submit_clearance'),
    path('view-clearance/', views.view_clearance, name='view_clearance'),
    path('staff-home/', views.staff_home, name='staff_home'),
    path('process-clearance/<int:section_id>/', views.process_clearance, name='process_clearance'),
    
]
