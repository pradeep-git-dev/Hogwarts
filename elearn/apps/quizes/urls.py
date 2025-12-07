from django.urls import path
from . import views

urlpatterns = [
    # Teacher actions
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('<int:quiz_id>/responses/', views.teacher_view_responses, name='teacher_view_responses'),

    # Password-protected start
    path('<int:quiz_id>/password/', views.quiz_password, name='quiz_password'),
    path('<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),

    # Common list
    path('', views.quiz_list, name='quiz_list'),

    # Student routes
    path('student/quizzes/', views.student_quiz_list, name='student_quiz_list'),
    path('student/quiz/<int:quiz_id>/', views.student_take_quiz, name='student_take_quiz'),
    path('student/quiz/<int:quiz_id>/result/', views.student_quiz_result, name='student_quiz_result'),
]
