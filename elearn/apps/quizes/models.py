from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    time_limit = models.IntegerField(default=10)

    questions_pdf = models.FileField(upload_to="quiz_pdfs/", blank=True, null=True)
    password = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('text', 'Written Answer'),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    text = models.CharField(max_length=300)

    # MCQ options (optional)
    option_a = models.CharField(max_length=200, blank=True, null=True)
    option_b = models.CharField(max_length=200, blank=True, null=True)
    option_c = models.CharField(max_length=200, blank=True, null=True)
    option_d = models.CharField(max_length=200, blank=True, null=True)

    correct_answer = models.CharField(max_length=200)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')

    def __str__(self):
        return self.text


class StudentResponse(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    student_answer = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.username} - {self.question.text}"


class QuizScore(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.score}"
