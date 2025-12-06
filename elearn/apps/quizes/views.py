from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import Quiz, Question, StudentResponse, QuizScore


# QUIZ LIST FOR ALL USERS
@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, "quiz_list.html", {"quizzes": quizzes})


# TEACHER — CREATE QUIZ
@login_required
def create_quiz(request):
    if not request.user.is_staff:
        return HttpResponse("Only teachers can create quizzes.")

    if request.method == "POST":
        title = request.POST["title"]
        time_limit = request.POST["time_limit"]
        password = request.POST["password"]
        pdf_file = request.FILES.get("pdf_file", None)

        quiz = Quiz.objects.create(
            teacher=request.user,
            title=title,
            time_limit=time_limit,
            password=password,
            questions_pdf=pdf_file,
        )

        return redirect("add_question", quiz_id=quiz.id)

    return render(request, "create_quiz.html")


# TEACHER — ADD QUESTIONS
@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.teacher:
        return HttpResponse("You are not allowed to modify this quiz.")

    if request.method == "POST":
        question_text = request.POST["text"]
        qtype = request.POST["question_type"]
        correct = request.POST["correct"]

        q = Question.objects.create(
            quiz=quiz,
            text=question_text,
            question_type=qtype,
            correct_answer=correct,
        )

        # Optional MCQ options
        q.option_a = request.POST.get("option_a")
        q.option_b = request.POST.get("option_b")
        q.option_c = request.POST.get("option_c")
        q.option_d = request.POST.get("option_d")
        q.save()

        if "add_more" in request.POST:
            return redirect("add_question", quiz_id=quiz.id)

        return redirect("quiz_list")

    return render(request, "add_question.html", {"quiz": quiz})


# ENTER PASSWORD BEFORE STARTING QUIZ
@login_required
def quiz_password(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        entered = request.POST["password"]
        if entered == quiz.password:
            return redirect("start_quiz", quiz_id=quiz.id)

        return render(request, "quiz_password.html", {
            "quiz": quiz,
            "error": "Incorrect password"
        })

    return render(request, "quiz_password.html", {"quiz": quiz})


# START QUIZ (DISPLAY QUESTIONS)
@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    return render(request, "start_quiz.html", {
        "quiz": quiz,
        "questions": questions,
    })


# SUBMIT QUIZ
@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    score = 0

    for q in questions:
        ans = request.POST.get(str(q.id), "")

        # MCQ auto-checking
        is_correct = False
        if q.question_type == "mcq":
            if ans.strip().lower() == q.correct_answer.strip().lower():
                is_correct = True
                score += 1

        StudentResponse.objects.create(
            student=request.user,
            quiz=quiz,
            question=q,
            student_answer=ans,
            is_correct=is_correct,
        )

    QuizScore.objects.create(
        student=request.user,
        quiz=quiz,
        score=score,
    )

    return redirect("quiz_result", quiz_id=quiz.id)


# STUDENT — QUIZ RESULTS
@login_required
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    score = QuizScore.objects.filter(student=request.user, quiz=quiz).last()
    responses = StudentResponse.objects.filter(student=request.user, quiz=quiz)

    return render(request, "quiz_result.html", {
        "quiz": quiz,
        "score": score,
        "responses": responses
    })


# TEACHER — VIEW ALL STUDENT SCORES
@login_required
def teacher_view_responses(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.teacher:
        return HttpResponse("Not allowed.")

    all_scores = QuizScore.objects.filter(quiz=quiz)

    return render(request, "teacher_responses.html", {
        "quiz": quiz,
        "scores": all_scores,
    })
