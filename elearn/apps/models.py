from django.db import models
from django.contrib.auth.models import User
from apps.classroom.models import Classroom


class Quiz(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_quizzes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.CharField(max_length=500)
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[
        ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")
    ])

    def __str__(self):
        return f"{self.quiz.title} - {self.text}"


class QuizScore(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="scores")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_scores")
    score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quiz', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.quiz.title}: {self.score}"
