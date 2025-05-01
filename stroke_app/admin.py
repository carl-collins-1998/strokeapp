from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    UserProfile, Patient, VitalSigns, LabResult, 
    ImagingStudy, NIHSSAssessment, Consultation, Alert
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'age', 'gender', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('first_name', 'last_name')
    date_hierarchy = 'created_at'

@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ('patient', 'systolic_bp', 'diastolic_bp', 'heart_rate', 'oxygen_saturation', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('patient__first_name', 'patient__last_name')
    date_hierarchy = 'timestamp'

@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('patient', 'cbc_normal', 'bmp_normal', 'coagulation_normal', 'timestamp')
    list_filter = ('cbc_normal', 'bmp_normal', 'coagulation_normal', 'timestamp')
    search_fields = ('patient__first_name', 'patient__last_name')
    date_hierarchy = 'timestamp'

@admin.register(ImagingStudy)
class ImagingStudyAdmin(admin.ModelAdmin):
    list_display = ('patient', 'study_type', 'result', 'timestamp')
    list_filter = ('study_type', 'result', 'timestamp')
    search_fields = ('patient__first_name', 'patient__last_name', 'description')
    date_hierarchy = 'timestamp'

@admin.register(NIHSSAssessment)
class NIHSSAssessmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'total_score', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('patient__first_name', 'patient__last_name', 'notes')
    date_hierarchy = 'timestamp'

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'status', 'diagnosis', 'requested_at', 'completed_at', 'tpa_recommended')
    list_filter = ('status', 'diagnosis', 'tpa_recommended', 'tpa_administered', 'requested_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'chief_complaint', 'other_recommendations', 'notes')
    date_hierarchy = 'requested_at'

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'priority', 'message', 'created_at', 'acknowledged')
    list_filter = ('alert_type', 'priority', 'acknowledged', 'created_at')
    search_fields = ('message', 'patient__first_name', 'patient__last_name')
    date_hierarchy = 'created_at'