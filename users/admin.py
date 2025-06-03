from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import User, StudentProfile, TutorProfile, Subject, Qualification,TutorAvailability, ConnectionRequest,Session  # Import models

# Register the User model with ImportExport functionality
@admin.register(User)
class UserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    search_fields = ('username', 'email')
    list_filter = ('role',)


# Register the StudentProfile model with ImportExport functionality
@admin.register(StudentProfile)
class StudentProfileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number', 'location', 'age')
    search_fields = ('user__username', 'full_name')
    list_filter = ('location',)


# Register the TutorProfile model with ImportExport functionality
@admin.register(TutorProfile)
class TutorProfileAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone_number', 'get_subjects', 'experience', 'rating')
    search_fields = ('user__username', 'full_name')
    list_filter = ('experience', 'rating')

    def get_subjects(self, obj):
        return ", ".join([subject.name for subject in obj.subjects_taught.all()])
    
    get_subjects.short_description = "Subjects Taught"


# Register the Subject model with ImportExport functionality
@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Qualification)
admin.site.register(TutorAvailability)
admin.site.register(ConnectionRequest)
admin.site.register(Session)