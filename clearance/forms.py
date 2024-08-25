from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, Staff, ClearanceDocument


class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
    ]
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, required=True)

    # Fields for students
    student_id = forms.CharField(max_length=20, required=False)
    year_of_study = forms.IntegerField(required=False)

    # Fields for staff
    department = forms.CharField(max_length=100, required=False)
    position = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name', 'user_type')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')

        if user_type == 'student':
            if not cleaned_data.get('student_id'):
                raise forms.ValidationError("Student ID is required for students.")
            if not cleaned_data.get('year_of_study'):
                raise forms.ValidationError("Year of study is required for students.")
        elif user_type == 'staff':
            if not cleaned_data.get('department'):
                raise forms.ValidationError("Department is required for staff.")
            if not cleaned_data.get('position'):
                raise forms.ValidationError("Position is required for staff.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            user_type = self.cleaned_data['user_type']
            if user_type == 'student':
                Student.objects.create(
                    user=user,
                    student_id=self.cleaned_data['student_id'],
                    year_of_study=self.cleaned_data['year_of_study'],
                    department=self.cleaned_data.get('department', '')
                )
            elif user_type == 'staff':
                Staff.objects.create(
                    user=user,
                    department=self.cleaned_data['department'],
                    position=self.cleaned_data['position']
                )
        return user

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = ClearanceDocument
        fields = ['document']