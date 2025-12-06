from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('<int:quiz_id>/start/', views.start_quiz, name='start_quiz'),
    path('<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('', views.quiz_list, name='quiz_list'),
    path('<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('<int:quiz_id>/password/', views.quiz_password, name='quiz_password'),
    path('<int:quiz_id>/responses/', views.teacher_view_responses, name='teacher_view_responses'),
]

]

