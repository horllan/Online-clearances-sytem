
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from .forms import CustomUserCreationForm
from .models import Notification, ClearanceForm, ClearanceSection, ClearanceDocument
from .forms import DocumentUploadForm

def user_logout(request):
    logout(request)
    return render(request, 'registration/logout.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'clearance/login.html')


@login_required
def home(request):
    if hasattr(request.user, 'student'):
        return render(request, 'clearance/student_dashboard.html')
    elif hasattr(request.user, 'staff'):
        return redirect('staff_dashboard')
    else:
        messages.warning(request, "Your account is not associated with a student or staff profile.")
        return redirect('logout')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}. You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'clearance/register.html', {'form': form})


@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')

    student = request.user.student
    clearance_forms = ClearanceForm.objects.filter(student=student).order_by('-created_at')
    latest_form = clearance_forms.first()

    if latest_form:
        sections = ClearanceSection.objects.filter(clearance_form=latest_form)
        completed_sections = sections.filter(status='cleared').count()
        total_sections = sections.count()
        progress_percentage = (completed_sections / total_sections) * 100 if total_sections > 0 else 0
    else:
        sections = []
        progress_percentage = 0

    context = {
        'clearance_forms': clearance_forms,
        'latest_form': latest_form,
        'sections': sections,
        'progress_percentage': progress_percentage,
    }
    return render(request, 'main/student_dashboard.html', context)


@login_required
def submit_clearance(request):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Only students can submit clearance forms.")
        return redirect('home')

    student = request.user.student
    existing_form = ClearanceForm.objects.filter(student=student, status='pending').first()

    if existing_form:
        messages.warning(request, "You already have a pending clearance form.")
        return redirect('view_clearance')

    if request.method == 'POST':
        clearance_form = ClearanceForm.objects.create(student=student)
        messages.success(request, "Clearance form submitted successfully.")
        return redirect('view_clearance')

    return render(request, 'clearance/submit_clearance.html')


@login_required
def view_clearance(request):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Only students can view clearance forms.")
        return redirect('home')

    student = request.user.student
    clearance_form = ClearanceForm.objects.filter(student=student).order_by('-created_at').first()

    if not clearance_form:
        messages.info(
            request, "You haven't submitted any clearance forms yet.")
        return redirect('submit_clearance')

    context = {
        'clearance_form': clearance_form,
        'sections': clearance_form.clearancesection_set.all()
    }
    return render(request, 'clearance/view_clearance.html', context)


@login_required
def staff_home(request):
    if not hasattr(request.user, 'staff'):
        messages.error(request, "This page is only accessible to staff members.")
        return redirect('home')
    staff = request.user.staff
    pending_sections = ClearanceSection.objects.filter(
        section=staff.department,
        status='pending'
    ).select_related('clearance_form__student')

    context = {'pending_sections': pending_sections}
    return render(request, 'clearance/staff_home.html', context)


@login_required
def process_clearance(request, section_id):
    if not hasattr(request.user, 'staff'):
        messages.error(request, "Only staff members can process clearance requests.")
        send_notification(section.clearance_form.student.user,
                          f"Your {section.get_section_display()} clearance has been approved.")
        return redirect('home')

    section = get_object_or_404(ClearanceSection, id=section_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')

        if action == 'approve':
            section.status = 'cleared'
            section.cleared_by = request.user.staff
            section.cleared_at = timezone.now()
            section.comments = comment
            messages.success(request, "Section approved successfully.")
            send_notification(section.clearance_form.student.user,
                              f"Your {section.get_section_display()} clearance has been approved.")
        elif action == 'reject':
            section.status = 'rejected'
            section.cleared_by = request.user.staff
            section.cleared_at = timezone.now()
            section.comments = comment
            messages.warning(request, "Section rejected.")
            send_notification(section.clearance_form.student.user,
                              f"Your {section.get_section_display()} clearance has been rejected. Reason: {comment}")
        else:
            messages.error(request, "Invalid action.")
            return redirect('staff_home')

        section.save()
        section.clearance_form.update_status()

        # Notification for overall clearance status
        if section.clearance_form.status == 'completed':
            send_notification(section.clearance_form.student.user,
                              "Congratulations! Your clearance process is complete.")
        elif section.clearance_form.status == 'rejected':
            send_notification(section.clearance_form.student.user,
                              "Your clearance form has been rejected. Please check the details and resubmit.")

        return redirect('staff_home')

    context = {
        'section': section,
        'student': section.clearance_form.student
    }
    return render(request, 'clearance/process_clearance.html', context)


@login_required
def review_clearance(request):
    staff = request.user.staff
    pending_sections = ClearanceSection.objects.filter(
        section=staff.department,
        is_cleared=False
    )
    return render(request, 'staff/review_clearance.html', {'pending_sections': pending_sections})


@login_required
def clear_student(request, section_id):
    section = ClearanceSection.objects.get(id=section_id)
    if request.method == 'POST':
        section.is_cleared = True
        section.cleared_by = request.user.staff
        section.cleared_date = timezone.now()
        section.save()
        return redirect('review_clearance')
    return render(request, 'staff/clear_student.html', {'section': section})


def send_notification(user, message):
    Notification.objects.create(user=user, message=message)


@login_required
def staff_dashboard(request):
    if not hasattr(request.user, 'staff'):
        return redirect('home')

    staff = request.user.staff
    pending_sections = ClearanceSection.objects.filter(
        section=staff.department,
        status='pending'
    ).select_related('clearance_form__student')

    recently_processed = ClearanceSection.objects.filter(
        section=staff.department,
        cleared_by=staff
    ).order_by('-cleared_at')[:5]

    context = {
        'pending_sections': pending_sections,
        'recently_processed': recently_processed,
    }
    return render(request, 'clearance/staff_dashboard.html', context)


@login_required
def notifications(request):
    user_notifications = request.user.notifications.all()
    unread_count = user_notifications.filter(is_read=False).count()

    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()

            context = {
                'notifications': user_notifications,
                'unread_count': unread_count,
            }
            return render(request, 'clearance/notifications.html', context)


@login_required
def upload_document(request, section_id):
    section = get_object_or_404(ClearanceSection, id=section_id)
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.student = request.user.student
            document.clearance_form = section.clearance_form
            document.section = section
            document.save()
            messages.success(request, "Document uploaded successfully.")
            return redirect('view_clearance')
    else:
        form = DocumentUploadForm()
    
    context = {
        'form': form,
        'section': section,
    }
    return render(request, 'main/upload_document.html', context)

@login_required
def verify_document(request, document_id):
    if not hasattr(request.user, 'staff'):
        messages.error(request, "You don't have permission to verify documents.")
        return redirect('home')

    document = get_object_or_404(ClearanceDocument, id=document_id)
    document.verified = True
    document.save()
    messages.success(request, "Document verified successfully.")
    return redirect('process_clearance', section_id=document.section.id)