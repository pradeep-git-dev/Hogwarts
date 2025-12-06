from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import random
import string

from .models import (
    Classroom, ClassMember, Attendance, Discussion, DiscussionReply,
    AnnouncementBoard, LearningResource, ProgressTracking
)
from apps.accounts.models import UserActivity, GamificationStats


# Classroom CRUD Operations

@login_required(login_url='login')
def create_classroom(request):
    """Create a new classroom"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        subject = request.POST.get('subject')
        grade_level = request.POST.get('grade_level')
        room_number = request.POST.get('room_number')
        schedule = request.POST.get('schedule')
        max_students = request.POST.get('max_students', 50)
        
        # Generate unique code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        classroom = Classroom.objects.create(
            teacher=request.user,
            name=name,
            description=description,
            subject=subject,
            grade_level=grade_level,
            room_number=room_number,
            schedule=schedule,
            max_students=int(max_students),
            code=code
        )
        
        if 'banner_image' in request.FILES:
            classroom.banner_image = request.FILES['banner_image']
            classroom.save()
        
        messages.success(request, f'Classroom "{name}" created successfully! Code: {code}')
        return redirect('classroom_detail', pk=classroom.id)
    
    return render(request, 'classroom/create_classroom.html')


@login_required(login_url='login')
def classroom_list(request):
    """List all classrooms for current user"""
    user = request.user
    
    if user.profile.role == 'teacher':
        classrooms = user.classrooms_taught.filter(status='active')
    else:
        classrooms = user.enrolled_classrooms.filter(status='active')
    
    context = {
        'classrooms': classrooms,
    }
    
    return render(request, 'classroom/classroom_list.html', context)


@login_required(login_url='login')
def classroom_detail(request, pk):
    """Display classroom details"""
    classroom = get_object_or_404(Classroom, id=pk)
    user = request.user
    
    # Check if user is teacher or enrolled student
    is_teacher = classroom.teacher == user
    is_member = ClassMember.objects.filter(classroom=classroom, student=user).exists()
    
    if not is_teacher and not is_member:
        messages.error(request, 'You do not have access to this classroom.')
        return redirect('classroom_list')
    
    # Get classroom data
    announcements = classroom.announcements.all()[:5]
    discussions = classroom.discussions.all()[:5]
    resources = classroom.resources.all()
    members = classroom.members.all()
    
    # Track activity
    UserActivity.objects.create(
        user=user,
        activity_type='resource_view',
        description=f'Viewed classroom: {classroom.name}'
    )
    
    context = {
        'classroom': classroom,
        'is_teacher': is_teacher,
        'is_member': is_member,
        'announcements': announcements,
        'discussions': discussions,
        'resources': resources,
        'members': members,
    }
    
    return render(request, 'classroom/classroom_detail.html', context)


@login_required(login_url='login')
def edit_classroom(request, pk):
    """Edit classroom details"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can edit this classroom.')
        return redirect('classroom_detail', pk=pk)
    
    if request.method == 'POST':
        classroom.name = request.POST.get('name', classroom.name)
        classroom.description = request.POST.get('description', classroom.description)
        classroom.subject = request.POST.get('subject', classroom.subject)
        classroom.grade_level = request.POST.get('grade_level', classroom.grade_level)
        classroom.room_number = request.POST.get('room_number', classroom.room_number)
        classroom.schedule = request.POST.get('schedule', classroom.schedule)
        classroom.max_students = int(request.POST.get('max_students', classroom.max_students))
        
        if 'banner_image' in request.FILES:
            classroom.banner_image = request.FILES['banner_image']
        
        classroom.save()
        
        messages.success(request, 'Classroom updated successfully!')
        return redirect('classroom_detail', pk=pk)
    
    context = {
        'classroom': classroom,
    }
    
    return render(request, 'classroom/edit_classroom.html', context)


@login_required(login_url='login')
def delete_classroom(request, pk):
    """Delete a classroom"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can delete this classroom.')
        return redirect('classroom_detail', pk=pk)
    
    if request.method == 'POST':
        classroom_name = classroom.name
        classroom.delete()
        messages.success(request, f'Classroom "{classroom_name}" has been deleted.')
        return redirect('classroom_list')
    
    context = {
        'classroom': classroom,
    }
    
    return render(request, 'classroom/delete_classroom.html', context)


# Classroom Member Management

@login_required(login_url='login')
def join_classroom(request):
    """Join classroom using code"""
    if request.method == 'POST':
        code = request.POST.get('code').upper()
        
        try:
            classroom = Classroom.objects.get(code=code)
        except Classroom.DoesNotExist:
            messages.error(request, 'Invalid classroom code.')
            return redirect('join_classroom')
        
        # Check if already a member
        if ClassMember.objects.filter(classroom=classroom, student=request.user).exists():
            messages.warning(request, 'You are already a member of this classroom.')
            return redirect('classroom_detail', pk=classroom.id)
        
        # Check capacity
        if classroom.is_full():
            messages.error(request, 'Classroom is full.')
            return redirect('join_classroom')
        
        # Add member
        ClassMember.objects.create(
            classroom=classroom,
            student=request.user,
            role='student'
        )
        
        # Create progress tracking
        ProgressTracking.objects.get_or_create(student=request.user, classroom=classroom)
        
        messages.success(request, f'Successfully joined {classroom.name}!')
        return redirect('classroom_detail', pk=classroom.id)
    
    return render(request, 'classroom/join_classroom.html')


@login_required(login_url='login')
def classroom_members(request, pk):
    """View classroom members"""
    classroom = get_object_or_404(Classroom, id=pk)
    user = request.user
    
    is_teacher = classroom.teacher == user
    is_member = ClassMember.objects.filter(classroom=classroom, student=user).exists()
    
    if not is_teacher and not is_member:
        messages.error(request, 'You do not have access to this classroom.')
        return redirect('classroom_list')
    
    members = classroom.members.filter(status='active').select_related('student')
    
    context = {
        'classroom': classroom,
        'members': members,
        'is_teacher': is_teacher,
    }
    
    return render(request, 'classroom/classroom_members.html', context)


@login_required(login_url='login')
def remove_member(request, pk, member_id):
    """Remove a student from classroom (teacher only)"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can remove members.')
        return redirect('classroom_detail', pk=pk)
    
    try:
        member = ClassMember.objects.get(classroom=classroom, id=member_id)
        student_name = member.student.get_full_name() or member.student.username
        member.status = 'dropped'
        member.save()
        messages.success(request, f'{student_name} has been removed from the classroom.')
    except ClassMember.DoesNotExist:
        messages.error(request, 'Member not found.')
    
    return redirect('classroom_members', pk=pk)


# Attendance Management

@login_required(login_url='login')
def mark_attendance(request, pk):
    """Mark attendance for students"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can mark attendance.')
        return redirect('classroom_detail', pk=pk)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        attendance_data = request.POST
        
        for key, value in attendance_data.items():
            if key.startswith('attendance_'):
                student_id = key.split('_')[1]
                status = value
                
                try:
                    student = User.objects.get(id=student_id)
                    attendance, created = Attendance.objects.get_or_create(
                        classroom=classroom,
                        student=student,
                        date=date,
                        defaults={
                            'status': status,
                            'recorded_by': request.user
                        }
                    )
                    if not created:
                        attendance.status = status
                        attendance.save()
                except User.DoesNotExist:
                    continue
        
        messages.success(request, 'Attendance marked successfully!')
        return redirect('classroom_detail', pk=pk)
    
    members = classroom.members.filter(status='active')
    today = timezone.now().date()
    
    context = {
        'classroom': classroom,
        'members': members,
        'today': today,
    }
    
    return render(request, 'classroom/mark_attendance.html', context)


@login_required(login_url='login')
def attendance_report(request, pk):
    """View attendance report for classroom"""
    classroom = get_object_or_404(Classroom, id=pk)
    user = request.user
    
    is_teacher = classroom.teacher == user
    is_member = ClassMember.objects.filter(classroom=classroom, student=user).exists()
    
    if not is_teacher and not is_member:
        messages.error(request, 'You do not have access to this classroom.')
        return redirect('classroom_list')
    
    # Get attendance stats
    attendance_records = Attendance.objects.filter(classroom=classroom)
    
    attendance_summary = attendance_records.values('student__username').annotate(
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late')),
        excused=Count('id', filter=Q(status='excused')),
        total=Count('id')
    ).order_by('student__username')
    
    context = {
        'classroom': classroom,
        'attendance_summary': attendance_summary,
        'is_teacher': is_teacher,
    }
    
    return render(request, 'classroom/attendance_report.html', context)


# Discussion Board

@login_required(login_url='login')
def create_discussion(request, pk):
    """Create a new discussion thread"""
    classroom = get_object_or_404(Classroom, id=pk)
    user = request.user
    
    is_member = ClassMember.objects.filter(classroom=classroom, student=user).exists()
    is_teacher = classroom.teacher == user
    
    if not is_member and not is_teacher:
        messages.error(request, 'You must be a member to post.')
        return redirect('classroom_detail', pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        topic = request.POST.get('topic', 'general')
        
        discussion = Discussion.objects.create(
            classroom=classroom,
            author=user,
            title=title,
            content=content,
            topic=topic
        )
        
        # Award points for discussion
        user.gamification_stats.add_points(10, "Created discussion")
        
        UserActivity.objects.create(
            user=user,
            activity_type='discussion_post',
            description=f'Created discussion: {title}'
        )
        
        messages.success(request, 'Discussion posted successfully!')
        return redirect('discussion_detail', classroom_id=pk, discussion_id=discussion.id)
    
    context = {
        'classroom': classroom,
    }
    
    return render(request, 'classroom/create_discussion.html', context)


@login_required(login_url='login')
def discussion_detail(request, classroom_id, discussion_id):
    """View discussion thread"""
    classroom = get_object_or_404(Classroom, id=classroom_id)
    discussion = get_object_or_404(Discussion, id=discussion_id, classroom=classroom)
    user = request.user
    
    # Increment views
    discussion.views_count += 1
    discussion.save()
    
    replies = discussion.replies.all()
    
    context = {
        'classroom': classroom,
        'discussion': discussion,
        'replies': replies,
    }
    
    return render(request, 'classroom/discussion_detail.html', context)


@login_required(login_url='login')
def reply_discussion(request, classroom_id, discussion_id):
    """Reply to a discussion thread"""
    classroom = get_object_or_404(Classroom, id=classroom_id)
    discussion = get_object_or_404(Discussion, id=discussion_id, classroom=classroom)
    user = request.user
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        reply = DiscussionReply.objects.create(
            discussion=discussion,
            author=user,
            content=content
        )
        
        # Award points for reply
        user.gamification_stats.add_points(5, "Posted discussion reply")
        
        UserActivity.objects.create(
            user=user,
            activity_type='discussion_post',
            description=f'Replied to discussion: {discussion.title}'
        )
        
        messages.success(request, 'Reply posted successfully!')
        return redirect('discussion_detail', classroom_id=classroom_id, discussion_id=discussion_id)
    
    context = {
        'classroom': classroom,
        'discussion': discussion,
    }
    
    return render(request, 'classroom/reply_discussion.html', context)


# Announcements

@login_required(login_url='login')
def create_announcement(request, pk):
    """Create classroom announcement"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can create announcements.')
        return redirect('classroom_detail', pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        is_pinned = request.POST.get('is_pinned') == 'on'
        
        AnnouncementBoard.objects.create(
            classroom=classroom,
            teacher=request.user,
            title=title,
            content=content,
            is_pinned=is_pinned
        )
        
        messages.success(request, 'Announcement posted!')
        return redirect('classroom_detail', pk=pk)
    
    context = {
        'classroom': classroom,
    }
    
    return render(request, 'classroom/create_announcement.html', context)


# Learning Resources

@login_required(login_url='login')
def upload_resource(request, pk):
    """Upload learning resource"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can upload resources.')
        return redirect('classroom_detail', pk=pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        resource_type = request.POST.get('resource_type')
        url = request.POST.get('url', '')
        
        resource = LearningResource.objects.create(
            classroom=classroom,
            uploaded_by=request.user,
            title=title,
            description=description,
            resource_type=resource_type,
            url=url
        )
        
        if 'file' in request.FILES:
            resource.file = request.FILES['file']
            resource.save()
        
        messages.success(request, 'Resource uploaded successfully!')
        return redirect('classroom_detail', pk=pk)
    
    context = {
        'classroom': classroom,
    }
    
    return render(request, 'classroom/upload_resource.html', context)


# Progress Tracking

@login_required(login_url='login')
def class_progress(request, pk):
    """View class progress analytics"""
    classroom = get_object_or_404(Classroom, id=pk)
    
    if classroom.teacher != request.user:
        messages.error(request, 'Only the teacher can view class progress.')
        return redirect('classroom_detail', pk=pk)
    
    # Get all students' progress
    progress_records = ProgressTracking.objects.filter(classroom=classroom)
    
    # Calculate class statistics
    avg_quiz_score = progress_records.aggregate(Avg('average_quiz_score'))['average_quiz_score__avg'] or 0
    avg_attendance = progress_records.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0
    
    context = {
        'classroom': classroom,
        'progress_records': progress_records,
        'avg_quiz_score': avg_quiz_score,
        'avg_attendance': avg_attendance,
    }
    
    return render(request, 'classroom/class_progress.html', context)


@login_required(login_url='login')
def student_progress(request, pk):
    """View individual student progress"""
    classroom = get_object_or_404(Classroom, id=pk)
    user = request.user
    
    is_teacher = classroom.teacher == user
    is_member = ClassMember.objects.filter(classroom=classroom, student=user).exists()
    
    if not is_teacher and not is_member:
        messages.error(request, 'You do not have access to this classroom.')
        return redirect('classroom_list')
    
    progress = get_object_or_404(ProgressTracking, classroom=classroom, student=user if not is_teacher else user)
    
    context = {
        'classroom': classroom,
        'progress': progress,
        'is_teacher': is_teacher,
    }
    
    return render(request, 'classroom/student_progress.html', context)
