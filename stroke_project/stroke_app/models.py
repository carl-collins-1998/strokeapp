from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# User role choices
ROLE_CHOICES = (
    ('technician', 'Mobile Stroke Technician'),
    ('neurologist', 'Remote Neurologist'),
    ('admin', 'Administrator'),
)

# User profile model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"

# Signal to create profile automatically when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, role='technician')  # Default role

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance, role='technician')  # Create if doesn't exist

# Patient model
class Patient(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    medical_history = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_patients')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.age} ({self.get_gender_display()})"

# Vital Signs model
class VitalSigns(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    systolic_bp = models.IntegerField(verbose_name="Systolic Blood Pressure (mmHg)")
    diastolic_bp = models.IntegerField(verbose_name="Diastolic Blood Pressure (mmHg)")
    heart_rate = models.IntegerField(verbose_name="Heart Rate (bpm)")
    respiratory_rate = models.IntegerField(verbose_name="Respiratory Rate (breaths/min)")
    temperature = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Temperature (°F)")
    oxygen_saturation = models.IntegerField(verbose_name="Oxygen Saturation (%)", 
                                          validators=[MinValueValidator(0), MaxValueValidator(100)])
    glucose = models.IntegerField(verbose_name="Blood Glucose (mg/dL)", null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Vitals for {self.patient} at {self.timestamp}"
    
    class Meta:
        verbose_name_plural = "Vital Signs"

# Lab Results model
class LabResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    cbc_normal = models.BooleanField(verbose_name="Complete Blood Count Normal", default=True)
    bmp_normal = models.BooleanField(verbose_name="Basic Metabolic Panel Normal", default=True)
    glucose_level = models.IntegerField(verbose_name="Glucose Level (mg/dL)", null=True, blank=True)
    coagulation_normal = models.BooleanField(verbose_name="Coagulation Studies Normal", default=True)
    inr_value = models.DecimalField(max_digits=3, decimal_places=1, verbose_name="INR Value", null=True, blank=True)
    platelet_count = models.IntegerField(verbose_name="Platelet Count", null=True, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Lab results for {self.patient} at {self.timestamp}"

# Imaging Study model
class ImagingStudy(models.Model):
    STUDY_TYPE_CHOICES = (
        ('CT', 'CT Scan'),
        ('MRI', 'MRI'),
        ('CTA', 'CT Angiogram'),
        ('MRA', 'MR Angiogram'),
    )
    RESULT_CHOICES = (
        ('ischemic', 'Ischemic Stroke'),
        ('hemorrhagic', 'Hemorrhagic Stroke'),
        ('normal', 'Normal'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='imaging_studies')
    study_type = models.CharField(max_length=10, choices=STUDY_TYPE_CHOICES)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    description = models.TextField()
    image_file = models.ImageField(upload_to='imaging_studies/', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.get_study_type_display()} for {self.patient} at {self.timestamp}"
    
    class Meta:
        verbose_name_plural = "Imaging Studies"

# NIHSS (National Institutes of Health Stroke Scale) Assessment
class NIHSSAssessment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='nihss_assessments')
    level_of_consciousness = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    loc_questions = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], 
                                      verbose_name="LOC Questions")
    loc_commands = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)], 
                                     verbose_name="LOC Commands")
    best_gaze = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)])
    visual = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    facial_palsy = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    motor_arm_left = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)])
    motor_arm_right = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)])
    motor_leg_left = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)])
    motor_leg_right = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)])
    limb_ataxia = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)])
    sensory = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)])
    best_language = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(3)])
    dysarthria = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)])
    extinction_inattention = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(2)])
    timestamp = models.DateTimeField(default=timezone.now)
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    @property
    def total_score(self):
        fields = [
            self.level_of_consciousness, self.loc_questions, self.loc_commands,
            self.best_gaze, self.visual, self.facial_palsy,
            self.motor_arm_left, self.motor_arm_right,
            self.motor_leg_left, self.motor_leg_right,
            self.limb_ataxia, self.sensory, self.best_language,
            self.dysarthria, self.extinction_inattention
        ]
        return sum(fields)
    
    def __str__(self):
        return f"NIHSS for {self.patient} - Score: {self.total_score} at {self.timestamp}"

# Consultation model
class Consultation(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    DIAGNOSIS_CHOICES = (
        ('ischemic_stroke', 'Acute Ischemic Stroke'),
        ('hemorrhagic_stroke', 'Acute Hemorrhagic Stroke'),
        ('tia', 'Transient Ischemic Attack'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_consultations')
    neurologist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performed_consultations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    chief_complaint = models.TextField()
    diagnosis = models.CharField(max_length=30, choices=DIAGNOSIS_CHOICES, null=True, blank=True)
    tpa_recommended = models.BooleanField(default=False)
    tpa_administered = models.BooleanField(default=False)
    tpa_time = models.DateTimeField(null=True, blank=True)
    other_recommendations = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Consultation for {self.patient} - {self.get_status_display()}"
    
    # Check if patient meets tPA criteria
    def meets_tpa_criteria(self):
        # Get the latest vital signs, lab results, etc.
        latest_vitals = self.patient.vital_signs.order_by('-timestamp').first()
        latest_labs = self.patient.lab_results.order_by('-timestamp').first()
        latest_imaging = self.patient.imaging_studies.order_by('-timestamp').first()
        latest_nihss = self.patient.nihss_assessments.order_by('-timestamp').first()
        
        # No data available
        if not latest_vitals or not latest_labs or not latest_imaging or not latest_nihss:
            return False, ["Incomplete patient data"]
        
        exclusion_reasons = []
        
        # Check NIHSS score
        if latest_nihss.total_score < 4:
            exclusion_reasons.append("NIHSS score < 4")
        
        # Check vital signs
        if latest_vitals.systolic_bp > 185:
            exclusion_reasons.append("Systolic BP > 185 mmHg")
        if latest_vitals.diastolic_bp > 110:
            exclusion_reasons.append("Diastolic BP > 110 mmHg")
        
        # Check glucose levels
        if latest_vitals.glucose is not None:
            if latest_vitals.glucose < 50 or latest_vitals.glucose > 400:
                exclusion_reasons.append(f"Blood glucose {latest_vitals.glucose} mg/dL (outside 50-400 range)")
        
        # Check lab results
        if latest_labs.inr_value is not None and latest_labs.inr_value > 1.7:
            exclusion_reasons.append(f"INR > 1.7 (current: {latest_labs.inr_value})")
        
        if latest_labs.platelet_count is not None and latest_labs.platelet_count < 100000:
            exclusion_reasons.append(f"Platelet count < 100,000/μL (current: {latest_labs.platelet_count})")
        
        # Check imaging results
        if latest_imaging.result == 'hemorrhagic':
            exclusion_reasons.append("Intracranial hemorrhage detected on imaging")
        
        if len(exclusion_reasons) == 0:
            return True, []
        else:
            return False, exclusion_reasons

# Alert model
class Alert(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    TYPE_CHOICES = (
        ('vital_signs', 'Abnormal Vital Signs'),
        ('lab_results', 'Critical Lab Results'),
        ('imaging', 'Imaging Results Ready'),
        ('consultation', 'Consultation Request'),
        ('tpa', 'tPA Decision Required'),
        ('system', 'System Alert'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    alert_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_priority_display()} Alert: {self.get_alert_type_display()} at {self.created_at}"