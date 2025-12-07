from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, StudentResponse, QuizScore


# ============================================================
# QUIZ LIST (COMMON)
# ============================================================
@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, "quiz_list.html", {"quizzes": quizzes})


# ============================================================
# TEACHER — CREATE QUIZ
# ============================================================
@login_required
def create_quiz(request):
    # IMPORTANT FIX: Use your role, NOT is_staff
    if request.user.profile.role != "teacher":
        return HttpResponse("Only teachers can create quizzes.")

    if request.method == "POST":
        quiz = Quiz.objects.create(
            teacher=request.user,
            title=request.POST["title"],
            time_limit=request.POST["time_limit"],
            password=request.POST["password"],
            questions_pdf=request.FILES.get("pdf_file")
        )
        return redirect("add_question", quiz_id=quiz.id)

    return render(request, "create_quiz.html")


# ============================================================
# TEACHER — ADD QUESTIONS
# ============================================================
@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.teacher:
        return HttpResponse("You are not allowed to modify this quiz.")

    if request.method == "POST":
        q = Question.objects.create(
            quiz=quiz,
            text=request.POST["text"],
            question_type=request.POST["question_type"],
            correct_answer=request.POST["correct"]
        )

        q.option_a = request.POST.get("option_a")
        q.option_b = request.POST.get("option_b")
        q.option_c = request.POST.get("option_c")
        q.option_d = request.POST.get("option_d")
        q.save()

        if "add_more" in request.POST:
            return redirect("add_question", quiz_id=quiz.id)

        return redirect("quiz_list")

    return render(request, "add_question.html", {"quiz": quiz})


# ============================================================
# PASSWORD PROTECTION
# ============================================================
@login_required
def quiz_password(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        if request.POST["password"] == quiz.password:
            return redirect("start_quiz", quiz_id=quiz.id)

        return render(request, "quiz_password.html", {
            "quiz": quiz,
            "error": "Incorrect password"
        })

    return render(request, "quiz_password.html", {"quiz": quiz})


# ============================================================
# START QUIZ
# ============================================================
@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    return render(request, "start_quiz.html", {
        "quiz": quiz,
        "questions": questions
    })


# ============================================================
# SUBMIT QUIZ
# ============================================================
@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    score = 0

    for q in questions:
        ans = request.POST.get(str(q.id), "")

        is_correct = (
            q.question_type == "mcq" 
            and ans.strip().lower() == q.correct_answer.strip().lower()
        )

        if is_correct:
            score += 1

        StudentResponse.objects.create(
            student=request.user,
            quiz=quiz,
            question=q,
            student_answer=ans,
            is_correct=is_correct
        )

    QuizScore.objects.create(
        student=request.user,
        quiz=quiz,
        score=score
    )

    return redirect("quiz_result", quiz_id=quiz.id)


# ============================================================
# STUDENT — SEE OWN RESULT
# ============================================================
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


# ============================================================
# TEACHER — VIEW ALL RESPONSES
# ============================================================
@login_required
def teacher_view_responses(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.teacher:
        return HttpResponse("Not allowed.")

    all_scores = QuizScore.objects.filter(quiz=quiz)

    return render(request, "teacher_responses.html", {
        "quiz": quiz,
        "scores": all_scores
    })


# ============================================================
# STUDENT — QUIZ LIST
# ============================================================
@login_required
def student_quiz_list(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, "student/student_quiz_list.html", {"quizzes": quizzes})


# ============================================================
# STUDENT — TAKE QUIZ
# ============================================================
@login_required
def student_take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    return redirect("quiz_password", quiz_id=quiz.id)


# ============================================================
# STUDENT — RESULT PAGE
# ============================================================
@login_required
def student_quiz_result(request, quiz_id):
    return quiz_result(request, quiz_id)
