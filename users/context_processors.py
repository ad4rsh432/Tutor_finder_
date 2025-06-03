from .models import TutorProfile

def tutor_profile_processor(request):
    if request.user.is_authenticated and hasattr(request.user, 'tutorprofile'):
        return {'profile': request.user.tutorprofile}
    return {}
