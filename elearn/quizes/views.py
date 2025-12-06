from django.shortcuts import render

from django.shortcuts import render, redirect
from .models import Quiz, Question, StudentAnswer, QuizResult
from django.contrib.auth.decorators import login_required

@login_required
def take_quiz(request, quiz_id, q_index=0):
    quiz = Quiz.objects.get(id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)
    total_questions = questions.count()

    # If all questions answered → show results
    if q_index >= total_questions:
        return redirect("quiz_result", quiz_id=quiz_id)

    current_question = questions[q_index]

    if request.method == "POST":
        answer = request.POST.get("answer")

        is_correct = (answer.strip().lower() == current_question.correct_answer.strip().lower())

        StudentAnswer.objects.create(
            student=request.user,
            question=current_question,
            selected_answer=answer,
            is_correct=is_correct
        )

        return redirect("take_quiz", quiz_id=quiz_id, q_index=q_index+1)

    return render(request, "take_quiz.html", {
        "quiz": quiz,
        "question": current_question,
        "q_index": q_index,
        "total_questions": total_questions
    })
@login_required
def quiz_result(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)
    answers = StudentAnswer.objects.filter(student=request.user, question__quiz=quiz)

    score = sum([1 for ans in answers if ans.is_correct])
    total = answers.count()

    QuizResult.objects.update_or_create(
        student=request.user,
        quiz=quiz,
        defaults={"score": score, "total": total}
    )

    return render(request, "quiz_result.html", {
        "quiz": quiz,
        "score": score,
        "total": total
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, StudentResponse, QuizScore
from django.utils import timezone


# -------------------------
# QUIZ LIST FOR STUDENTS & TEACHERS
# -------------------------
@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, 'quiz_list.html', {"quizzes": quizzes})



# -------------------------
# CREATE QUIZ (TEACHER ONLY)
# -------------------------
@login_required
def create_quiz(request):
    if not request.user.is_staff:
        return HttpResponse("Only teachers can create quizzes")

    if request.method == "POST":
        title = request.POST['title']
        time_limit = request.POST['time_limit']
        password = request.POST['password']
        pdf_file = request.FILES.get('pdf_file')

        quiz = Quiz.objects.create(
            teacher=request.user,
            title=title,
            time_limit=time_limit,
            password=password,
            questions_pdf=pdf_file
        )

        return redirect('add_question', quiz_id=quiz.id)

    return render(request, 'create_quiz.html')



# -------------------------
# ADD QUESTION (TEACHER ONLY)
# -------------------------
@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.teacher:
        return HttpResponse("Not allowed")

    if request.method == "POST":
        question_text = request.POST['text']
        qtype = request.POST['question_type']
        corr = request.POST['correct']

        q = Question.objects.create(
            quiz=quiz,
            text=question_text,
            question_type=qtype,
            correct_answer=corr
        )

        # MCQ OPTIONS (optional)
        q.option_a = request.POST.get('option_a')
        q.option_b = request.POST.get('option_b')
        q.option_c = request.POST.get('option_c')
        q.option_d = request.POST.get('option_d')
        q.save()

        if "add_more" in request.POST:
            return redirect('add_question', quiz_id=quiz.id)

        return redirect('quiz_list')

    return render(request, 'add_question.html', {"quiz": quiz})



# -------------------------
# ENTER PASSWORD TO ACCESS QUIZ
# -------------------------
@login_required
def quiz_password(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == "POST":
        entered = request.POST['password']
        if entered == quiz.password:
            return redirect('start_quiz', quiz_id=quiz_id)
        else:
            return render(request, 'quiz_password.html', {"quiz": quiz, "error": "Wrong password"})

    return render(request, 'quiz_password.html', {"quiz": quiz})



# -------------------------
# START QUIZ
# -------------------------
@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    return render(request, 'start_quiz.html', {
        "quiz": quiz,
        "questions": questions
    })



# -------------------------
# SUBMIT QUIZ
# -------------------------
@login_required
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    score = 0

    for q in questions:
        answer = request.POST.get(str(q.id), "")

        is_correct = False
        if q.question_type == 'mcq':
            if answer.strip().lower() == q.correct_answer.strip().lower():
                is_correct = True
                score += 1

        StudentResponse.objects.create(
            student=request.user,
            quiz=quiz,
            question=q,
            student_answer=answer,
            is_correct=is_correct
        )

    QuizScore.objects.create(
        student=request.user,
        quiz=quiz,
        score=score
    )

    return redirect('quiz_result', quiz_id=quiz_id)


@login_required
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    score = QuizScore.objects.filter(student=request.user, quiz=quiz).last()
    responses = StudentResponse.objects.filter(student=request.user, quiz=quiz)

    return render(request, 'quiz_result.html', {
        "quiz": quiz,
        "score": score,
        "responses": responses
    })



# -------------------------
# TEACHER VIEW ALL STUDENT RESPONSES
# -------------------------
@login_required
def teacher_view_responses(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.user != quiz.teacher:
        return HttpResponse("Not allowed")

    all_scores = QuizScore.objects.filter(quiz=quiz)
    return render(request, 'teacher_responses.html', {
        "quiz": quiz,
        "scores": all_scores
    })

