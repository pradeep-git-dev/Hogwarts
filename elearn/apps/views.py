from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Quiz, Question, QuizScore
from apps.classroom.models import Classroom


# ============================================================
#   TEACHER — CREATE QUIZ
# ============================================================
@login_required
def create_quiz(request, classroom_id):
    # Only teachers allowed
    if request.user.profile.role != "teacher":
        messages.error(request, "Only teachers can create quizzes.")
        return redirect("dashboard")

    classroom = get_object_or_404(Classroom, id=classroom_id)

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")

        if not title:
            messages.error(request, "Quiz title is required.")
            return redirect("create_quiz", classroom_id=classroom_id)

        quiz = Quiz.objects.create(
            classroom=classroom,
            title=title,
            description=description,
            created_by=request.user
        )

        messages.success(request, "Quiz created! Add questions now.")
        return redirect("add_questions", quiz_id=quiz.id)

    return render(request, "teacher/quiz_create.html", {
        "classroom": classroom
    })


# ============================================================
#   TEACHER — ADD QUESTIONS
# ============================================================
@login_required
def add_questions(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user.profile.role != "teacher":
        messages.error(request, "Only teachers can add questions.")
        return redirect("dashboard")

    if request.method == "POST":
        text = request.POST.get("text")
        option_a = request.POST.get("option_a")
        option_b = request.POST.get("option_b")
        option_c = request.POST.get("option_c")
        option_d = request.POST.get("option_d")
        correct = request.POST.get("correct_answer")

        if not text or not correct:
            messages.error(request, "All fields are required.")
            return redirect("add_questions", quiz_id=quiz.id)

        Question.objects.create(
            quiz=quiz,
            text=text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct
        )

        messages.success(request, "Question added.")
        return redirect("add_questions", quiz_id=quiz.id)

    return render(request, "teacher/quiz_questions.html", {
        "quiz": quiz,
        "questions": quiz.questions.all()
    })


# ============================================================
#   STUDENT — TAKE QUIZ
# ============================================================
@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    # Prevent teachers from taking quizzes
    if request.user.profile.role == "teacher":
        messages.error(request, "Teachers cannot take quizzes.")
        return redirect("dashboard")

    return render(request, "student/take_quiz.html", {
        "quiz": quiz,
        "questions": questions
    })


# ============================================================
#   STUDENT — SUBMIT QUIZ
# ============================================================
@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.all()

    # Block teachers
    if request.user.profile.role == "teacher":
        messages.error(request, "Teachers cannot submit quizzes.")
        return redirect("dashboard")

    score = 0
    for q in questions:
        user_answer = request.POST.get(str(q.id))
        if user_answer and user_answer == q.correct_answer:
            score += 1

    QuizScore.objects.update_or_create(
        quiz=quiz,
        student=request.user,
        defaults={"score": score}
    )

    messages.success(request, "Quiz submitted successfully!")
    return redirect("quiz_results", quiz_id=quiz.id)


# ============================================================
#   STUDENT — RESULTS
# ============================================================
@login_required
def quiz_results(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    score_obj = QuizScore.objects.filter(quiz=quiz, student=request.user).first()

    if not score_obj:
        messages.error(request, "You haven't taken this quiz yet.")
        return redirect("take_quiz", quiz_id=quiz.id)

    return render(request, "student/quiz_results.html", {
        "quiz": quiz,
        "score": score_obj.score,
        "total": quiz.questions.count()
    })
