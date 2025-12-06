from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Avg

import random
import string

from .models import (
    Classroom, ClassMember, Attendance, Discussion, DiscussionReply,
    AnnouncementBoard, LearningResource, ProgressTracking
)

# ---------------------------------------------------------
# CLASSROOM CRUD
# ---------------------------------------------------------

@login_required
def create_classroom(request):
    if request.method == "POST":
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        classroom = Classroom.objects.create(
            teacher=request.user,
            name=request.POST['name'],
            description=request.POST.get('description'),
            subject=request.POST.get('subject'),
            grade_level=request.POST.get('grade_level'),
            room_number=request.POST.get('room_number'),
            schedule=request.POST.get('schedule'),
            max_students=int(request.POST.get('max_students', 50)),
            code=code,
        )

        if 'banner_image' in request.FILES:
            classroom.banner_image = request.FILES['banner_image']
            classroom.save()

        messages.success(request, f"Classroom created successfully! Code: {code}")
        return redirect("classroom_detail", classroom_id=classroom.id)

    return render(request, "classroom/create_classroom.html")


@login_required
def classroom_list(request):
    user = request.user

    # Teacher vs student logic
    if hasattr(user, "profile") and user.profile.role == "teacher":
        classrooms = user.classrooms_taught.filter(status="active")
    else:
        classrooms = user.enrolled_classrooms.filter(status="active")

    return render(request, "classroom/classroom_list.html", {"classrooms": classrooms})


@login_required
def classroom_detail(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    user = request.user

    is_teacher = classroom.teacher == user
    is_member = ClassMember.objects.filter(classroom=classroom, student=user).exists()

    if not (is_teacher or is_member):
        messages.error(request, "You are not part of this classroom.")
        return redirect("classroom_list")

    context = {
        "classroom": classroom,
        "is_teacher": is_teacher,
        "announcements": classroom.announcements.all()[:5],
        "discussions": classroom.discussions.all()[:5],
        "resources": classroom.resources.all(),
        "members": classroom.members.filter(status="active"),
    }

    return render(request, "classroom/classroom_detail.html", context)


@login_required
def edit_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Only the teacher can edit this classroom.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    if request.method == "POST":
        for f in ["name", "description", "subject", "grade_level", "room_number", "schedule"]:
            setattr(classroom, f, request.POST.get(f, getattr(classroom, f)))

        classroom.max_students = int(request.POST.get("max_students", classroom.max_students))

        if "banner_image" in request.FILES:
            classroom.banner_image = request.FILES["banner_image"]

        classroom.save()
        messages.success(request, "Classroom updated.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    return render(request, "classroom/edit_classroom.html", {"classroom": classroom})


@login_required
def delete_classroom(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Only the teacher can delete the classroom.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    if request.method == "POST":
        name = classroom.name
        classroom.delete()
        messages.success(request, f"Classroom '{name}' deleted.")
        return redirect("classroom_list")

    return render(request, "classroom/delete_classroom.html", {"classroom": classroom})


# ---------------------------------------------------------
# CLASSROOM MEMBERSHIP
# ---------------------------------------------------------

@login_required
def join_classroom(request):
    if request.method == "POST":
        code = request.POST.get("code", "").upper()

        try:
            classroom = Classroom.objects.get(code=code)
        except Classroom.DoesNotExist:
            messages.error(request, "Invalid classroom code.")
            return redirect("join_classroom")

        if classroom.is_full():
            messages.error(request, "Classroom is full.")
            return redirect("join_classroom")

        ClassMember.objects.get_or_create(
            classroom=classroom,
            student=request.user,
            defaults={"role": "student"}
        )

        ProgressTracking.objects.get_or_create(student=request.user, classroom=classroom)

        messages.success(request, f"Joined classroom {classroom.name}")
        return redirect("classroom_detail", classroom_id=classroom.id)

    return render(request, "classroom/join_classroom.html")


@login_required
def classroom_members(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user and not ClassMember.objects.filter(student=request.user, classroom=classroom).exists():
        messages.error(request, "You are not allowed to view members.")
        return redirect("classroom_list")

    members = classroom.members.filter(status="active")
    return render(request, "classroom/classroom_members.html", {"classroom": classroom, "members": members})


@login_required
def remove_member(request, classroom_id, member_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Only the teacher can remove members.")
        return redirect("classroom_members", classroom_id=classroom_id)

    member = get_object_or_404(ClassMember, id=member_id, classroom=classroom)

    member.status = "dropped"
    member.save()

    messages.success(request, f"Removed {member.student.username} from the classroom.")
    return redirect("classroom_members", classroom_id=classroom_id)


# ---------------------------------------------------------
# ATTENDANCE
# ---------------------------------------------------------

@login_required
def mark_attendance(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Only the teacher can mark attendance.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    if request.method == "POST":
        date = request.POST.get("date")

        for key, value in request.POST.items():
            if key.startswith("attendance_"):
                student_id = key.split("_")[1]
                student = User.objects.get(id=student_id)

                attendance, created = Attendance.objects.get_or_create(
                    classroom=classroom,
                    student=student,
                    date=date,
                    defaults={"status": value, "recorded_by": request.user}
                )

                if not created:
                    attendance.status = value
                    attendance.save()

        messages.success(request, "Attendance updated.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    members = classroom.members.filter(status="active")
    today = timezone.now().date()

    return render(request, "classroom/mark_attendance.html", {
        "classroom": classroom,
        "members": members,
        "today": today,
    })


@login_required
def attendance_report(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    records = Attendance.objects.filter(classroom=classroom).values(
        "student__username"
    ).annotate(
        present=Count("id", filter=Q(status="present")),
        absent=Count("id", filter=Q(status="absent")),
        late=Count("id", filter=Q(status="late")),
        excused=Count("id", filter=Q(status="excused")),
        total=Count("id"),
    )

    return render(request, "classroom/attendance_report.html", {
        "classroom": classroom,
        "records": records,
    })


# ---------------------------------------------------------
# DISCUSSIONS
# ---------------------------------------------------------

@login_required
def create_discussion(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if request.method == "POST":
        Discussion.objects.create(
            classroom=classroom,
            author=request.user,
            title=request.POST["title"],
            content=request.POST["content"],
            topic=request.POST.get("topic", "general"),
        )

        messages.success(request, "Discussion created.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    return render(request, "classroom/create_discussion.html", {"classroom": classroom})


@login_required
def discussion_detail(request, classroom_id, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, classroom_id=classroom_id)

    discussion.views_count += 1
    discussion.save()

    replies = discussion.replies.all()

    return render(request, "classroom/discussion_detail.html", {
        "classroom_id": classroom_id,
        "discussion": discussion,
        "replies": replies,
    })


@login_required
def reply_discussion(request, classroom_id, discussion_id):
    discussion = get_object_or_404(Discussion, id=discussion_id, classroom_id=classroom_id)

    if request.method == "POST":
        DiscussionReply.objects.create(
            discussion=discussion,
            author=request.user,
            content=request.POST["content"]
        )

        messages.success(request, "Reply posted.")
        return redirect("discussion_detail", classroom_id=classroom_id, discussion_id=discussion_id)

    return render(request, "classroom/reply_discussion.html", {"discussion": discussion})


# ---------------------------------------------------------
# ANNOUNCEMENTS
# ---------------------------------------------------------

@login_required
def create_announcement(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Only teachers can post announcements.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    if request.method == "POST":
        AnnouncementBoard.objects.create(
            classroom=classroom,
            teacher=request.user,
            title=request.POST["title"],
            content=request.POST["content"],
            is_pinned=("is_pinned" in request.POST),
        )

        messages.success(request, "Announcement posted.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    return render(request, "classroom/create_announcement.html", {"classroom": classroom})


# ---------------------------------------------------------
# LEARNING RESOURCES
# ---------------------------------------------------------

@login_required
def upload_resource(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Not allowed.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    if request.method == "POST":
        resource = LearningResource.objects.create(
            classroom=classroom,
            uploaded_by=request.user,
            title=request.POST["title"],
            description=request.POST.get("description"),
            resource_type=request.POST["resource_type"],
            url=request.POST.get("url"),
        )

        if "file" in request.FILES:
            resource.file = request.FILES["file"]
            resource.save()

        messages.success(request, "Resource uploaded!")
        return redirect("classroom_detail", classroom_id=classroom_id)

    return render(request, "classroom/upload_resource.html", {"classroom": classroom})


# ---------------------------------------------------------
# PROGRESS
# ---------------------------------------------------------

@login_required
def class_progress(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if classroom.teacher != request.user:
        messages.error(request, "Only teachers can view analytics.")
        return redirect("classroom_detail", classroom_id=classroom_id)

    progress_records = ProgressTracking.objects.filter(classroom=classroom)

    avg_score = progress_records.aggregate(Avg("average_quiz_score"))["average_quiz_score__avg"] or 0
    avg_attendance = progress_records.aggregate(Avg("completion_percentage"))["completion_percentage__avg"] or 0

    return render(request, "classroom/class_progress.html", {
        "classroom": classroom,
        "progress_records": progress_records,
        "avg_score": avg_score,
        "avg_attendance": avg_attendance,
    })


@login_required
def student_progress(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    progress = get_object_or_404(ProgressTracking, classroom=classroom, student=request.user)

    return render(request, "classroom/student_progress.html", {
        "classroom": classroom,
        "progress": progress,
    })
