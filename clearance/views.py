
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm


@login_required
def home(request):
    if hasattr(request.user, 'student'):
        return render(request, 'clearance/student_home.html')
    elif hasattr(request.user, 'staff'):
        return render(request, 'clearance/staff_home.html')
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
    return render(request, 'main/staff_home.html', context)


@login_required
def process_clearance(request, section_id):
    if not hasattr(request.user, 'staff'):
        messages.error(request, "Only staff members can process clearance requests.")
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
        elif action == 'reject':
            section.status = 'rejected'
            section.cleared_by = request.user.staff
            section.cleared_at = timezone.now()
            section.comments = comment
            messages.warning(request, "Section rejected.")
        else:
            messages.error(
                request, "Invalid action.")
            return redirect('staff_home')

        section.save()
        section.clearance_form.update_status()
        return redirect('staff_home')

    context = {
                'section': section,
                'student': section.clearance_form.student
            }
    return render(request, 'main/process_clearance.html', context)
