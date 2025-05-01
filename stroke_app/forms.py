from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (
    UserProfile, Patient, VitalSigns, LabResult, 
    ImagingStudy, NIHSSAssessment, Consultation, Alert
)

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone']

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'age', 'gender', 'medical_history']

class VitalSignsForm(forms.ModelForm):
    class Meta:
        model = VitalSigns
        fields = ['systolic_bp', 'diastolic_bp', 'heart_rate', 
                  'respiratory_rate', 'temperature', 'oxygen_saturation', 'glucose']

class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabResult
        fields = ['cbc_normal', 'bmp_normal', 'glucose_level', 
                  'coagulation_normal', 'inr_value', 'platelet_count', 'notes']

class ImagingStudyForm(forms.ModelForm):
    class Meta:
        model = ImagingStudy
        fields = ['study_type', 'result', 'description', 'image_file']

class NIHSSAssessmentForm(forms.ModelForm):
    class Meta:
        model = NIHSSAssessment
        fields = [
            'level_of_consciousness', 'loc_questions', 'loc_commands',
            'best_gaze', 'visual', 'facial_palsy',
            'motor_arm_left', 'motor_arm_right',
            'motor_leg_left', 'motor_leg_right',
            'limb_ataxia', 'sensory', 'best_language',
            'dysarthria', 'extinction_inattention', 'notes'
        ]

class ConsultationRequestForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['chief_complaint']

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'tpa_recommended', 'tpa_administered', 
                  'tpa_time', 'other_recommendations', 'notes']
        widgets = {
            'tpa_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ['priority', 'alert_type', 'message']