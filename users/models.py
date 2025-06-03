from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username


# Subject Model (Shared by Students & Tutors)
class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Tutor Availability Model (Time Slots)
class TutorAvailability(models.Model):
    tutor = models.ForeignKey("TutorProfile", on_delete=models.CASCADE, related_name="availability_slots")
    day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])
    start_time = models.TimeField(default="09:00:00")  # ✅ Default start time
    end_time = models.TimeField(default="17:00:00")  # ✅ Default end time

    def __str__(self):
        return f"{self.tutor.user.username}: {self.day_of_week} ({self.start_time} - {self.end_time})"


# Qualifications Model
class Qualification(models.Model):
    tutor = models.ForeignKey("TutorProfile", on_delete=models.CASCADE, related_name="qualifications")
    degree = models.CharField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    year_completed = models.PositiveIntegerField(default=2000)

    def __str__(self):
        return f"{self.degree} - {self.tutor.user.username}"


# Student Profile Model
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    connected_tutors = models.ManyToManyField("TutorProfile", related_name="connected_students", blank=True, default="")
    full_name = models.CharField(max_length=255, default="Unknown")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='static/profile_pics/students/', blank=True, null=True)
    subjects_interested = models.ManyToManyField(Subject, related_name="interested_students")
    age = models.IntegerField(default=0)
    location = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(default='')
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)



    def __str__(self):
        return f"{self.user.username} (Student)"


# Tutor Profile Model
class TutorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, default="Unknown")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='static/profile_pics/tutors/', blank=True, null=True)
    subjects_taught = models.ManyToManyField(Subject, related_name="tutors")
    experience = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    location = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True, default="")
    age = models.IntegerField(blank=True, null=True, default=0)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)


    def __str__(self):
        return f"{self.user.username} (Tutor)"


class ConnectionRequest(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} → {self.tutor.user.username} ({self.status})"



class ConnectionRequest(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """ Auto-connect student and tutor when approved """
        super().save(*args, **kwargs)
        if self.status == "approved":
            self.student.connected_tutors.add(self.tutor)

    def __str__(self):
        return f"{self.student.user.username} → {self.tutor.user.username} ({self.status})"

class Session(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("completed", "Completed"),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    meeting_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.student} - {self.tutor} ({self.status})"
    


class Rating(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE)  # Ensure one rating per session
    student = models.ForeignKey("StudentProfile", on_delete=models.CASCADE)
    tutor = models.ForeignKey(TutorProfile, on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveIntegerField()  # 1 to 5 scale
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for {self.tutor.full_name}"
