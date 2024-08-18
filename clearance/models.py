from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    year_of_study = models.IntegerField()
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id}"


class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department} ({self.position})"


class ClearanceForm(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def create_sections(self):
        for section, _ in ClearanceSection.SECTION_CHOICES:
            ClearanceSection.objects.create(clearance_form=self, section=section)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.create_sections()

    def __str__(self):
        return f"Clearance Form for {self.student.user.get_full_name()}"

    def get_overall_status(self):
        sections = self.clearancesection_set.all()
        if all(section.status == 'cleared' for section in sections):
            return 'completed'
        elif any(section.status == 'rejected' for section in sections):
            return 'rejected'
        elif any(section.status == 'in_progress' for section in sections):
            return 'in_progress'
        else:
            return 'pending'

    def update_status(self):
        self.status = self.get_overall_status()
        self.save()


class ClearanceSection(models.Model):
    SECTION_CHOICES = [
        ('library', 'Library'),
        ('laboratory',
         'Laboratory'),
        ('department',
         'Department'),
        ('senate',
         'Senate'),
        ('hostel',
         'Hostel'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress',
         'In Progress'),
        ('cleared',
         'Cleared'),
        ('rejected',
         'Rejected'),
    ]

    clearance_form = models.ForeignKey(
        ClearanceForm, on_delete=models.CASCADE)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    cleared_by = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_section_display()} - {self.get_status_display()}"

        def clear(self, staff):
            self.status = 'cleared'
            self.cleared_by = staff
            self.cleared_at = timezone.now()
            self.save()
            self.clearance_form.update_status()

            def reject(self, staff, comment):
                self.status = 'rejected'
                self.cleared_by = staff
                self.cleared_at = timezone.now()
                self.comments = comment
                self.save()
                self.clearance_form.update_status()
