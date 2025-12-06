from django.urls import path
from . import views

urlpatterns = [
    # Classroom CRUD
    path('create/', views.create_classroom, name='create_classroom'),
    path('list/', views.classroom_list, name='classroom_list'),
    path('<int:pk>/', views.classroom_detail, name='classroom_detail'),
    path('<int:pk>/edit/', views.edit_classroom, name='edit_classroom'),
    path('<int:pk>/delete/', views.delete_classroom, name='delete_classroom'),
    
    # Join Classroom
    path('join/', views.join_classroom, name='join_classroom'),
    
    # Classroom Members
    path('<int:pk>/members/', views.classroom_members, name='classroom_members'),
    path('<int:pk>/members/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    
    # Attendance
    path('<int:pk>/attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('<int:pk>/attendance/report/', views.attendance_report, name='attendance_report'),
    
    # Discussions
    path('<int:pk>/discussion/create/', views.create_discussion, name='create_discussion'),
    path('<int:classroom_id>/discussion/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),
    path('<int:classroom_id>/discussion/<int:discussion_id>/reply/', views.reply_discussion, name='reply_discussion'),
    
    # Announcements
    path('<int:pk>/announcement/create/', views.create_announcement, name='create_announcement'),
    
    # Learning Resources
    path('<int:pk>/resources/upload/', views.upload_resource, name='upload_resource'),
    
    # Progress
    path('<int:pk>/progress/class/', views.class_progress, name='class_progress'),
    path('<int:pk>/progress/student/', views.student_progress, name='student_progress'),
]
