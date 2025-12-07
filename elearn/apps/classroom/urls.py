from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_classroom, name='create_classroom'),
    path('', views.classroom_list, name='classroom_list'),
    path('<int:classroom_id>/', views.classroom_detail, name='classroom_detail'),
    path('<int:classroom_id>/edit/', views.edit_classroom, name='edit_classroom'),
    path('<int:classroom_id>/delete/', views.delete_classroom, name='delete_classroom'),
    path('join/', views.join_classroom, name='join_classroom'),
    path('<int:classroom_id>/members/', views.classroom_members, name='classroom_members'),
    path('<int:classroom_id>/members/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    path('<int:classroom_id>/attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('<int:classroom_id>/attendance/report/', views.attendance_report, name='attendance_report'),
    path('<int:classroom_id>/discussion/create/', views.create_discussion, name='create_discussion'),
    path('<int:classroom_id>/discussion/<int:discussion_id>/', views.discussion_detail, name='discussion_detail'),
    path('<int:classroom_id>/discussion/<int:discussion_id>/reply/', views.reply_discussion, name='reply_discussion'),
    path('<int:classroom_id>/announcement/create/', views.create_announcement, name='create_announcement'),
    path('<int:classroom_id>/resources/upload/', views.upload_resource, name='upload_resource'),
    path('<int:classroom_id>/progress/class/', views.class_progress, name='class_progress'),
    path('<int:classroom_id>/progress/student/', views.student_progress, name='student_progress'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
]
