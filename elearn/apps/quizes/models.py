from django.db import models
from django.db import models
from django.contrib.auth.models import User


QUESTION_TYPES = (
    ('mcq', 'Multiple Choice'),
    ('fitb', 'Fill in the Blank'),
)

class Quiz(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    # Time limit in minutes
    time_limit = models.IntegerField(default=10)

    # Teacher uploads questions PDF (optional)
    questions_pdf = models.FileField(upload_to='quiz_pdfs/', blank=True, null=True)

    # Password protected exam
    password = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

    text = models.CharField(max_length=300)

    # Optional MCQ fields
    option_a = models.CharField(max_length=200, blank=True, null=True)
    option_b = models.CharField(max_length=200, blank=True, null=True)
    option_c = models.CharField(max_length=200, blank=True, null=True)
    option_d = models.CharField(max_length=200, blank=True, null=True)

    # For MCQ or fill-in-the-blank
    correct_answer = models.CharField(max_length=200)

    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('text', 'Written Answer'),
    )
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='mcq')

    def __str__(self):
        return self.text



class StudentAnswer(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class QuizResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)
from django.db import models
from django.contrib.auth.models import User


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

    text = models.CharField(max_length=300)

    # Optional MCQ fields
    option_a = models.CharField(max_length=200, blank=True, null=True)
    option_b = models.CharField(max_length=200, blank=True, null=True)
    option_c = models.CharField(max_length=200, blank=True, null=True)
    option_d = models.CharField(max_length=200, blank=True, null=True)

    # For MCQ or fill-in-the-blank
    correct_answer = models.CharField(max_length=200)

    QUESTION_TYPES = (
        ('mcq', 'Multiple Choice'),
        ('text', 'Written Answer'),
    )
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
        return f"{self.student.username} - {self.question}"


class QuizScore(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.score}"

