from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, TutorProfile, Subject, Qualification

class StudentRegisterForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
        required=True
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
        required=True
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat your password'}),
    )
    subjects_interested = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5',
            'style': 'height:auto;'
        }),
        required=True,
        help_text='Hold Ctrl/Cmd to select multiple subjects.'
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your address', 'rows': '3'}),
        required=True
    )
    location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City / Area'}),
        required=True
    )
    age = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your age'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone_number', 'subjects_interested', 'address', 'location', 'age', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'  # Assign student role

        if commit:
            user.save()

            # Debugging: Print cleaned data to check if age exists
            print("Cleaned Data:", self.cleaned_data)

            student_profile, created = StudentProfile.objects.get_or_create(user=user)

            student_profile.full_name = self.cleaned_data['full_name']
            student_profile.phone_number = self.cleaned_data['phone_number']
            student_profile.address = self.cleaned_data['address']
            student_profile.location = self.cleaned_data['location']

            # ✅ Safely handle missing `age` field
            student_profile.age = self.cleaned_data.get('age', None)  # Use `.get()` to avoid KeyError

            student_profile.save()

            # ✅ Set ManyToManyField (Subjects)
            student_profile.subjects_interested.set(self.cleaned_data['subjects_interested'])
            student_profile.save()

        return user





class TutorRegisterForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
        required=True
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
        required=True
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat your password'}),
    )
    subjects_taught = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '5',
            'style': 'height:auto;'
        }),
        required=True,
        help_text='Hold Ctrl/Cmd to select multiple subjects.'
    )
    experience = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of experience'}),
        required=True
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your address', 'rows': '3'}),
        required=True
    )
    age = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Your age'}),
        required=True
    )
    degree = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Degree (e.g., BSc in Math)'}),
        required=True
    )
    institution = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University / Institution name'}),
        required=True
    )
    year_completed = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year completed (e.g. 2022)'}),
        required=True
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'full_name', 'phone_number', 'subjects_taught',
            'experience', 'address', 'age', 'degree', 'institution', 'year_completed', 'password1', 'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'tutor'  # Assuming you have a custom role field
        
        if commit:
            user.save()

            # ✅ Check if a profile already exists before creating a new one
            tutor_profile, created = TutorProfile.objects.get_or_create(user=user)

            # ✅ Update profile fields instead of creating a duplicate
            tutor_profile.full_name = self.cleaned_data['full_name']
            tutor_profile.phone_number = self.cleaned_data['phone_number']
            tutor_profile.experience = self.cleaned_data['experience']
            tutor_profile.age = self.cleaned_data.get('age', None)
            tutor_profile.address = self.cleaned_data.get('address', "")
            
            # ✅ Set subjects for ManyToManyField
            tutor_profile.subjects_taught.set(self.cleaned_data['subjects_taught'])
            
            tutor_profile.save()

        return user

