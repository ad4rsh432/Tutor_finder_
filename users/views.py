from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import StudentRegisterForm, TutorRegisterForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import StudentProfile, TutorProfile, Qualification, Subject, TutorAvailability, ConnectionRequest, Session,Rating
from django.utils.timezone import now
import qrcode
from datetime import datetime
from io import BytesIO
import base64
import json
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from datetime import datetime, timedelta
from django.contrib import messages
import json
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from datetime import datetime
from django.utils.timezone import make_aware
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Distance in km


def student_register(request):
    subjects = Subject.objects.all()  # ✅ Pass subjects to the template

    if request.method == "POST":
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('student_dashboard')  # Redirect to student dashboard after registration
    else:
        form = StudentRegisterForm()

    return render(request, "users/student_register.html", {"form": form, "subjects": subjects})

def tutor_register(request):
    if request.method == "POST":
        form = TutorRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in after registration
            return redirect('tutor_dashboard')  # Redirect to tutor dashboard
    else:
        form = TutorRegisterForm()
    return render(request, "users/tutor_register.html", {"form": form})



def mark_completed_sessions():
    sessions = Session.objects.filter(status='scheduled', end_time__lt=timezone.now())
    sessions.update(status='completed', is_completed=True)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    query = request.GET.get('subject', '')  # Get the subject from the form
    tutors = []

    if query:
        tutors = TutorProfile.objects.filter(subjects_taught__name__icontains=query)[:3]  # Limit to 3 tutors

    return render(request, 'users/home.html', {
        'query': query,
        'tutors': tutors
    })


@login_required
def dashboard_redirect(request):
    """Redirect students and tutors to their respective dashboards after login."""
    if request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'tutor':
        return redirect('tutor_dashboard')
    else:
        return redirect('home')  # Default redirect if role is undefined
    
@login_required
def student_dashboard(request):
    student = request.user.studentprofile

    # Ensure student has location data
    if student.latitude is None or student.longitude is None:
        return render(request, 'users/student_dashboard.html', {
            'student': student,
            'connected_tutors': student.connected_tutors.all(),
            'pending_requests': ConnectionRequest.objects.filter(student=student, status='pending'),
            'upcoming_sessions': Session.objects.filter(student=student, scheduled_time__gte=now(), status='approved').order_by('scheduled_time'),
            'nearby_tutors': [],  # No tutors can be found without student location
            'error_message': "⚠️ Please update your location to find nearby tutors."
        })

    connected_tutors = student.connected_tutors.all()
    pending_requests = ConnectionRequest.objects.filter(student=student, status='pending')
    upcoming_sessions = Session.objects.filter(student=student, scheduled_time__gte=now(), status='approved').order_by('scheduled_time')

    # Fetch tutors sorted by proximity
    nearby_tutors = []
    for tutor in TutorProfile.objects.exclude(user=student.user):
        # Skip tutors without location
        if tutor.latitude is None or tutor.longitude is None:
            continue
        
        distance = calculate_distance(student.latitude, student.longitude, tutor.latitude, tutor.longitude)
        if distance <= 20:  # Limit to 20 km radius
            nearby_tutors.append((tutor, round(distance, 2)))  # Store tutor & distance
    
    nearby_tutors.sort(key=lambda x: x[1])  # Sort by closest first

    return render(request, 'users/student_dashboard.html', {
        'student': student,
        'connected_tutors': connected_tutors,
        'pending_requests': pending_requests,
        'upcoming_sessions': upcoming_sessions,
        'nearby_tutors': nearby_tutors
    })


@login_required
def tutor_dashboard(request):
    tutor = request.user.tutorprofile

    if tutor.latitude is None or tutor.longitude is None:
        messages.warning(request, "Your location is not set. Please update your profile to see nearby students.")
        nearby_students = []  # If tutor's location is missing, don't process nearby students
    else:
        nearby_students = []
        for student in StudentProfile.objects.exclude(latitude=None, longitude=None):
            distance = calculate_distance(tutor.latitude, tutor.longitude, student.latitude, student.longitude)
            if distance <= 20:  # Limit to 20 km radius
                nearby_students.append((student, distance))
        
        nearby_students.sort(key=lambda x: x[1])  # Sort by closest first
        nearby_students = [s[0] for s in nearby_students]  # Extract only student objects

    connection_requests = ConnectionRequest.objects.filter(tutor=tutor, status='pending')
    upcoming_sessions = Session.objects.filter(tutor=tutor, status__in=["approved", "pending"]).order_by("scheduled_time")
    previous_sessions = Session.objects.filter(tutor=tutor, status="completed").order_by("scheduled_time")
    pending_sessions = Session.objects.filter(tutor=tutor, status="pending").count()

    return render(request, 'users/tutor_dashboard.html', {
        'tutor': tutor,
        'connection_requests': connection_requests,
        'upcoming_sessions': upcoming_sessions,
        'pending_sessions': pending_sessions,
        'previous_sessions': previous_sessions,
        'nearby_students': nearby_students
    })



@csrf_exempt
@login_required
def update_location(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.user

        if hasattr(user, 'studentprofile'):
            profile = user.studentprofile
        elif hasattr(user, 'tutorprofile'):
            profile = user.tutorprofile
        else:
            return JsonResponse({'error': 'Profile not found'}, status=400)

        profile.latitude = data.get('latitude')
        profile.longitude = data.get('longitude')
        profile.save()

        return JsonResponse({'success': True})


@login_required
def student_profile_view(request):
    user = request.user
    if user.role != 'student':
        return redirect('tutor_profile')  # Redirect tutors if they try to access student profile

    profile, created = StudentProfile.objects.get_or_create(user=user)
    all_subjects = Subject.objects.all()
    
    # Fetch connected tutors
    connected_tutors = profile.connected_tutors.all()

    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.age = request.POST.get('age', profile.age)
        profile.location = request.POST.get('location', profile.location)
        profile.address = request.POST.get('address', profile.address)
        profile.bio = request.POST.get('bio', profile.bio)
        date_of_birth_str = request.POST.get('date_of_birth', None)
        if date_of_birth_str:
            try:
                profile.date_of_birth = datetime.strptime(date_of_birth_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return redirect('student_profile')

        # ✅ Update ManyToManyField `subjects_interested`
        selected_subjects = request.POST.getlist('subjects_interested')  
        profile.subjects_interested.set(selected_subjects)  

        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        return redirect('student_profile')

    return render(request, 'users/student_profile.html', {
        'profile': profile,
        'all_subjects': all_subjects,
        'connected_tutors': connected_tutors
    })


@login_required
def send_connection_request(request, tutor_id):
    student = request.user.studentprofile
    tutor = TutorProfile.objects.get(id=tutor_id)
    
    if not ConnectionRequest.objects.filter(student=student, tutor=tutor).exists():
        ConnectionRequest.objects.create(student=student, tutor=tutor)
    
    return redirect('student_dashboard')

@login_required
def approve_connection_request(request, request_id):
    connection_request = ConnectionRequest.objects.get(id=request_id)
    
    if request.user.tutorprofile == connection_request.tutor:
        connection_request.status = 'approved'
        connection_request.save()
        # Add student to tutor's connected list
        connection_request.student.connected_tutors.add(connection_request.tutor)
    
    return redirect('tutor_dashboard')


@login_required
def schedule_session(request, tutor_id):
    student = request.user.studentprofile
    tutor = TutorProfile.objects.get(id=tutor_id)

    if request.method == "POST":
        subject_id = request.POST.get('subject')
        scheduled_time = request.POST.get('scheduled_time')
        subject = Subject.objects.get(id=subject_id)

        Session.objects.create(
            student=student,
            tutor=tutor,
            subject=subject,
            scheduled_time=scheduled_time
        )

        return redirect('student_dashboard')

    return render(request, 'users/schedule_session.html', {
        'tutor': tutor,
        'subjects': tutor.subjects_taught.all(),
    })




@login_required
def tutor_profile_view(request):
    user = request.user
    if user.role != 'tutor':
        return redirect('student_profile')  # Redirect students if they try to access tutor profile

    profile, created = TutorProfile.objects.get_or_create(user=user)
    all_subjects = Subject.objects.all()
    qualification, created = Qualification.objects.get_or_create(tutor=profile)
    availability, created = TutorAvailability.objects.get_or_create(tutor=profile)
    day_of_week_choices = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.phone_number = request.POST.get('phone_number', profile.phone_number)
        profile.experience = request.POST.get('experience', profile.experience)
        # profile.hourly_rate = request.POST.get('hourly_rate', profile.hourly_rate)
        hourly_rate = request.POST.get('hourly_rate', profile.hourly_rate)
        profile.hourly_rate = None if hourly_rate == "" else hourly_rate
        profile.location = request.POST.get('location', profile.location)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.date_of_birth = request.POST.get('date_of_birth', profile.date_of_birth)
        # ✅ Fix: Update ManyToManyField `subjects_taught`
        selected_subjects = request.POST.getlist('subjects_taught')  # Get list of selected subject IDs
        profile.subjects_taught.set(selected_subjects)  # Correct way to update M2M field

        qualification.degree = request.POST.get('degree', qualification.degree)
        qualification.institution = request.POST.get('institution', qualification.institution)
        qualification.year_completed = request.POST.get('year_completed', qualification.year_completed)

        availability.day_of_week = request.POST.get('day_of_week',availability.day_of_week)
        availability.start_time = request.POST.get('start_time',availability.start_time)
        availability.end_time = request.POST.get('end_time',availability.end_time)

        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        qualification.save()
        availability.save()
        return redirect('tutor_profile')

    return render(request, 'users/tutor_profile.html', {'profile': profile, 'all_subjects':all_subjects, 'availability':availability, 'qualification':qualification,'day_of_week_choices': day_of_week_choices,})



@login_required
def search_tutors(request):
    """ Search tutors based on name, subject, or location """
    query = request.GET.get('q', '')
    student_profile = StudentProfile.objects.get(user=request.user)  # Get the logged-in student
    connected_tutors = student_profile.connected_tutors.all()  # Fetch connected tutors

    tutors = TutorProfile.objects.all()
    
    if query:
        tutors = tutors.filter(
            Q(user__username__icontains=query) |
            Q(subjects_taught__name__icontains=query) |
            Q(location__icontains=query)
        ).distinct()

    return render(request, 'users/search_tutors.html', {
        'tutors': tutors,
        'query': query,
        'connected_tutors': connected_tutors,  # Pass connected tutors to template
    })

@login_required
def send_connection_request(request, tutor_id):
    """ Student sends a connection request to a tutor """
    student = get_object_or_404(StudentProfile, user=request.user)
    tutor = get_object_or_404(TutorProfile, id=tutor_id)

    # Prevent duplicate requests
    existing_request = ConnectionRequest.objects.filter(student=student, tutor=tutor, status='pending').exists()
    if not existing_request:
        ConnectionRequest.objects.create(student=student, tutor=tutor, status='pending')

    return redirect('student_dashboard')

@login_required
def approve_connection_request(request, request_id):
    """ Tutor approves a student's connection request """
    connection_request = get_object_or_404(ConnectionRequest, id=request_id)

    if request.user == connection_request.tutor.user:
        connection_request.status = 'approved'
        connection_request.save()

    return redirect('tutor_dashboard')

def mark_completed_sessions():
    sessions = Session.objects.filter(status='scheduled', end_time__lt=timezone.now())
    sessions.update(status='completed', is_completed=True)

@login_required
def book_session_view(request):
    student_profile = request.user.studentprofile
    connected_tutors = student_profile.connected_tutors.all()

    subjects = Subject.objects.all()
    selected_subject = request.GET.get('subject')

    if selected_subject:
        try:
            subject_obj = Subject.objects.get(id=selected_subject)
            available_tutors = connected_tutors.filter(subjects_taught=subject_obj)
        except Subject.DoesNotExist:
            available_tutors = []
    else:
        available_tutors = connected_tutors

    return render(request, 'users/book_session.html', {
        'connected_tutors': available_tutors,
        'subjects': subjects,
        'selected_subject': selected_subject
    })

def view_tutor_profile(request, tutor_id):
    tutor = get_object_or_404(TutorProfile, id=tutor_id)
    return render(request, "users/view_tutor.html", {"tutor": tutor})

# @login_required
# def request_session_view(request, tutor_id):
#     student_profile = request.user.studentprofile
#     tutor_profile = get_object_or_404(TutorProfile, id=tutor_id)

#     if request.method == "POST":
#         subject_id = request.POST.get('subject')
#         scheduled_time = request.POST.get('scheduled_time')
#         end_time = request.POST.get('end_time')

#         subject = get_object_or_404(Subject, id=subject_id)

#         session = Session.objects.create(
#             student=student_profile,
#             tutor=tutor_profile,
#             subject=subject,
#             scheduled_time=scheduled_time,
#             end_time=end_time,
#             status="pending",
#         )

#         # Notify tutor (e.g., email notification can be added)
#         return redirect('student_dashboard')

#     return render(request, 'users/request_session.html', {'tutor': tutor_profile})

@login_required
def request_session_view(request, tutor_id):
    tutor = get_object_or_404(TutorProfile, id=tutor_id)
    subjects_t = tutor.subjects_taught.all()
    student = get_object_or_404(StudentProfile, user=request.user)

    if request.method == "POST":
        session_date = request.POST.get("session_date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        subject_id = request.POST.get("subject_id")  # Make sure this is received

        print("Received Data:", session_date, start_time, end_time, subject_id)  # Debugging

        if not session_date or not start_time or not end_time or not subject_id:
            return JsonResponse({"status": "error", "message": "All fields are required."}, status=400)

        try:
            subject = Subject.objects.get(id=subject_id)
            scheduled_time = make_aware(datetime.strptime(f"{session_date} {start_time}", "%Y-%m-%d %H:%M"))
            end_time = make_aware(datetime.strptime(f"{session_date} {end_time}", "%Y-%m-%d %H:%M"))

            if scheduled_time >= end_time:
                return JsonResponse({"status": "error", "message": "End time must be after start time."}, status=400)

            session = Session.objects.create(
                student=student,
                tutor=tutor,
                subject=subject,
                scheduled_time=scheduled_time,
                end_time=end_time,
                status="pending"
            )

            print("Session Created:", session)  # Debugging

            return JsonResponse({"status": "success", "message": "Session request submitted!"})

        except Subject.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid subject."}, status=400)
        except ValueError as e:
            return JsonResponse({"status": "error", "message": f"Invalid input: {str(e)}"}, status=400)

    return render(request, "users/request_session.html", {"tutor": tutor, "subjects_t":subjects_t})


@login_required
def tutor_sessions_view(request):
    tutor_profile = request.user.tutorprofile
    pending_sessions = Session.objects.filter(tutor=tutor_profile, status="pending")

    return render(request, 'users/tutor_sessions.html', {"pending_sessions": pending_sessions})

@login_required
def approve_session(request, session_id):
    session = get_object_or_404(Session, id=session_id, tutor=request.user.tutorprofile)
    session.status = "approved"
    session.save()
    return redirect("tutor_sessions")

@login_required
def session_details(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    # Check if the logged-in user is the tutor
    is_tutor = request.user.is_authenticated and hasattr(request.user, 'tutorprofile') and request.user.tutorprofile == session.tutor

    if is_tutor and request.method == "POST":
        meeting_link = request.POST.get("meeting_link")
        session.meeting_link = meeting_link
        session.save()
        return redirect("session_details", session_id=session.id)

    return render(request, "users/session_details.html", {"session": session, "is_tutor": is_tutor})



@login_required
def student_sessions_view(request):
    student_profile = request.user.studentprofile
    upcoming_sessions = Session.objects.filter(student=student_profile, status="approved").order_by("scheduled_time")
    completed_sessions = Session.objects.filter(student=student_profile, status="completed").order_by("-scheduled_time")

    return render(request, 'users/student_sessions.html', {
        "upcoming_sessions": upcoming_sessions,
        "completed_sessions": completed_sessions
    })


@login_required
def mark_session_completed(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    # Ensure the logged-in user is the tutor of the session
    if request.user != session.tutor.user:
        messages.error(request, "You are not authorized to update this session.")
        return redirect("tutor_dashboard")  # Redirect to tutor dashboard

    # Mark the session as completed
    session.status = "completed"
    session.save()

    messages.success(request, "Session marked as completed successfully.")
    return redirect("tutor_dashboard")  # Redirect back to tutor's dashboard



@login_required
def rate_tutor(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    # Ensure only the student who attended can rate
    if request.user != session.student.user:
        messages.error(request, "You are not allowed to rate this session.")
        return redirect("session_details", session_id=session.id)

    # Ensure the session is completed before allowing rating
    if session.status != "completed":
        messages.error(request, "You can only rate completed sessions.")
        return redirect("session_details", session_id=session.id)

    # Prevent duplicate ratings
    existing_rating = Rating.objects.filter(session=session).first()
    if existing_rating:
        messages.error(request, "You have already rated this session.")
        return redirect("session_details", session_id=session.id)

    if request.method == "POST":
        rating_value = int(request.POST.get("rating"))
        feedback = request.POST.get("feedback", "")

        if 1 <= rating_value <= 5:
            # Create Rating entry
            rating = Rating.objects.create(
                session=session,
                student=session.student,
                tutor=session.tutor,
                rating=rating_value,
                feedback=feedback,
            )

            # Update tutor's average rating
            all_ratings = Rating.objects.filter(tutor=session.tutor).values_list("rating", flat=True)
            session.tutor.rating = sum(all_ratings) / len(all_ratings)  # Average rating
            session.tutor.save()

            messages.success(request, "Thank you for your feedback!")
        else:
            messages.error(request, "Invalid rating. Please select a value between 1 and 5.")

    return redirect("session_details", session_id=session.id)