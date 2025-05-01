from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse

from .models import (
    UserProfile, Patient, VitalSigns, LabResult, ImagingStudy, 
    NIHSSAssessment, Consultation, Alert
)
from .forms import (
    UserRegisterForm, UserProfileForm, PatientForm, VitalSignsForm, 
    LabResultForm, ImagingStudyForm, NIHSSAssessmentForm, 
    ConsultationRequestForm, ConsultationForm, AlertForm
)

# Debug view for troubleshooting
def debug_view(request):
    context = {
        'title': 'Debug Page',
        'time': timezone.now()
    }
    return render(request, 'debug.html', context)

# Decorators
def technician_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'technician':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You don't have permission to access this page.")
    return _wrapped_view

def neurologist_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'neurologist':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You don't have permission to access this page.")
    return _wrapped_view

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You don't have permission to access this page.")
    return _wrapped_view

# Authentication views
# def register(request):
#     if request.method == 'POST':
#         user_form = UserRegisterForm(request.POST)
#         profile_form = UserProfileForm(request.POST)
#         if user_form.is_valid() and profile_form.is_valid():
#             user = user_form.save()
#             profile = profile_form.save(commit=False)
#             profile.user = user
#             profile.save()
            
#             messages.success(request, f'Account created successfully. You can now log in.')
#             return redirect('login')
#     else:
#         user_form = UserRegisterForm()
#         profile_form = UserProfileForm()
    
#     return render(request, 'registration/register.html', {
#         'user_form': user_form,
#         'profile_form': profile_form
#     })

def register(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            
            # Instead of creating a new profile, update the existing one
            # that was created by the signal
            try:
                profile = user.profile
                profile.role = profile_form.cleaned_data['role']
                profile.phone = profile_form.cleaned_data['phone']
                profile.save()
            except UserProfile.DoesNotExist:
                # Just in case the signal didn't work for some reason
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            
            messages.success(request, f'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        user_form = UserRegisterForm()
        profile_form = UserProfileForm()
    
    return render(request, 'registration/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def technician_or_admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role in ['technician', 'admin']:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You don't have permission to access this page.")
    return _wrapped_view

# Home view
def home(request):
    if request.user.is_authenticated:
        try:
            user_profile = request.user.profile
            role = user_profile.role
            
            # Get unacknowledged alerts
            alerts = Alert.objects.filter(acknowledged=False)
            
            context = {
                'alerts': alerts[:5],  # Limit to 5 alerts
                'role': role,  # Add role to context for template
            }
            
            # Role-specific context
            if role == 'technician':
                # Show recent patients and consultations
                patients = Patient.objects.filter(created_by=request.user).order_by('-created_at')[:5]
                consultations = Consultation.objects.filter(requested_by=request.user).order_by('-requested_at')[:5]
                
                context.update({
                    'patients': patients,
                    'consultations': consultations,
                })
            
            elif role == 'neurologist':
                # Show pending consultations
                pending_consultations = Consultation.objects.filter(
                    Q(status='requested') | Q(neurologist=request.user, status='in_progress')
                ).order_by('-requested_at')[:10]
                
                context.update({
                    'pending_consultations': pending_consultations,
                })
            
            elif role == 'admin':
                # Show system stats
                total_patients = Patient.objects.count()
                total_consultations = Consultation.objects.count()
                active_users = User.objects.filter(last_login__gte=timezone.now() - timezone.timedelta(days=7)).count()
                
                context.update({
                    'total_patients': total_patients,
                    'total_consultations': total_consultations,
                    'active_users': active_users,
                })
                
            return render(request, 'home.html', context)
            
        except UserProfile.DoesNotExist:
            # Create a default profile or show a message
            return render(request, 'profile_setup.html', {
                'no_profile': True,
                'message': 'Please complete your profile setup'
            })
    else:
        # User is not authenticated
        return render(request, 'home.html', {'not_authenticated': True})

# Profile setup view  
def profile_setup(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        
        # Create profile for the user
        UserProfile.objects.create(
            user=request.user,
            role=role,
            phone=phone
        )
        
        messages.success(request, "Profile set up successfully!")
        return redirect('home')
    
    return render(request, 'profile_setup.html')

# Patient views
@login_required
def patient_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        ).order_by('-created_at')
    else:
        patients = Patient.objects.all().order_by('-created_at')
    
    paginator = Paginator(patients, 10)
    page = request.GET.get('page')
    patients_page = paginator.get_page(page)
    
    return render(request, 'patients/patient_list.html', {'patients': patients_page, 'search_query': search_query})

@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    vitals = patient.vital_signs.order_by('-timestamp')
    lab_results = patient.lab_results.order_by('-timestamp')
    imaging_studies = patient.imaging_studies.order_by('-timestamp')
    nihss_assessments = patient.nihss_assessments.order_by('-timestamp')
    consultations = patient.consultations.order_by('-requested_at')
    
    # Get the latest data
    latest_vitals = vitals.first()
    latest_labs = lab_results.first()
    latest_imaging = imaging_studies.first()
    latest_nihss = nihss_assessments.first()
    
    context = {
        'patient': patient,
        'vitals': vitals[:5],  # Limit to 5 recent entries
        'lab_results': lab_results[:5],
        'imaging_studies': imaging_studies[:5],
        'nihss_assessments': nihss_assessments[:5],
        'consultations': consultations,
        'latest_vitals': latest_vitals,
        'latest_labs': latest_labs,
        'latest_imaging': latest_imaging,
        'latest_nihss': latest_nihss,
    }
    
    return render(request, 'patients/patient_detail.html', context)

# @login_required
# @technician_required
# def patient_create(request):
#     if request.method == 'POST':
#         form = PatientForm(request.POST)
#         if form.is_valid():
#             patient = form.save(commit=False)
#             patient.created_by = request.user
#             patient.save()
#             messages.success(request, f'Patient {patient.first_name} {patient.last_name} created successfully!')
#             return redirect('patient_detail', pk=patient.pk)
#     else:
#         form = PatientForm()
    
#     return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Add New Patient'})

@login_required
@technician_or_admin_required  # Replace @technician_required with this
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.save()
            messages.success(request, f'Patient {patient.first_name} {patient.last_name} created successfully!')
            return redirect('patient_detail', pk=patient.pk)
    else:
        form = PatientForm()
    
    return render(request, 'patients/patient_form.html', {'form': form, 'title': 'Add New Patient'})

@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Patient information updated successfully!')
            return redirect('patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'patients/patient_form.html', {
        'form': form, 
        'title': f'Edit Patient: {patient.first_name} {patient.last_name}'
    })

# Vital Signs views
@login_required
@technician_or_admin_required
def vitals_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = VitalSignsForm(request.POST)
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.patient = patient
            vitals.recorded_by = request.user
            vitals.save()
            
            # Check for critical values and create alerts
            if vitals.systolic_bp > 185 or vitals.diastolic_bp > 110:
                Alert.objects.create(
                    patient=patient,
                    priority='high',
                    alert_type='vital_signs',
                    message=f'Critical BP: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg'
                )
            
            if vitals.oxygen_saturation < 92:
                Alert.objects.create(
                    patient=patient,
                    priority='high',
                    alert_type='vital_signs',
                    message=f'Low O2 Saturation: {vitals.oxygen_saturation}%'
                )
            
            if vitals.glucose is not None and (vitals.glucose < 50 or vitals.glucose > 400):
                Alert.objects.create(
                    patient=patient,
                    priority='high',
                    alert_type='vital_signs',
                    message=f'Critical Blood Glucose: {vitals.glucose} mg/dL'
                )
            
            messages.success(request, 'Vital signs recorded successfully!')
            return redirect('patient_detail', pk=patient_id)
    else:
        form = VitalSignsForm()
    
    return render(request, 'patients/vitals_form.html', {
        'form': form,
        'patient': patient
    })

# Lab Results views
@login_required
@technician_or_admin_required
def lab_results_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = LabResultForm(request.POST)
        if form.is_valid():
            lab_result = form.save(commit=False)
            lab_result.patient = patient
            lab_result.recorded_by = request.user
            lab_result.save()
            
            # Create alerts for abnormal lab values
            alert_messages = []
            if not lab_result.cbc_normal:
                alert_messages.append("Abnormal Complete Blood Count")
            
            if not lab_result.bmp_normal:
                alert_messages.append("Abnormal Basic Metabolic Panel")
            
            if not lab_result.coagulation_normal:
                alert_messages.append("Abnormal Coagulation Studies")
            
            if lab_result.inr_value and lab_result.inr_value > 1.7:
                alert_messages.append(f"Elevated INR: {lab_result.inr_value}")
            
            if lab_result.platelet_count and lab_result.platelet_count < 100000:
                alert_messages.append(f"Low Platelet Count: {lab_result.platelet_count}")
            
            if alert_messages:
                Alert.objects.create(
                    patient=patient,
                    priority='medium',
                    alert_type='lab_results',
                    message="Critical Lab Results: " + ", ".join(alert_messages)
                )
            
            messages.success(request, 'Lab results recorded successfully!')
            return redirect('patient_detail', pk=patient_id)
    else:
        form = LabResultForm()
    
    return render(request, 'patients/lab_results_form.html', {
        'form': form,
        'patient': patient
    })

# Imaging Study views
@login_required
@technician_or_admin_required
def imaging_study_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = ImagingStudyForm(request.POST, request.FILES)
        if form.is_valid():
            imaging = form.save(commit=False)
            imaging.patient = patient
            imaging.recorded_by = request.user
            imaging.save()
            
            # Create alert for imaging results
            priority = 'medium'
            if imaging.result == 'hemorrhagic':
                priority = 'critical'
                message = f"CRITICAL: Hemorrhagic stroke detected on {imaging.get_study_type_display()}"
            elif imaging.result == 'ischemic':
                priority = 'high'
                message = f"Ischemic stroke detected on {imaging.get_study_type_display()}"
            else:
                message = f"New {imaging.get_study_type_display()} results available"
            
            Alert.objects.create(
                patient=patient,
                priority=priority,
                alert_type='imaging',
                message=message
            )
            
            messages.success(request, 'Imaging study recorded successfully!')
            return redirect('patient_detail', pk=patient_id)
    else:
        form = ImagingStudyForm()
    
    return render(request, 'patients/imaging_form.html', {
        'form': form,
        'patient': patient
    })

# NIHSS Assessment views
@login_required
@technician_or_admin_required
def nihss_assessment_create(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = NIHSSAssessmentForm(request.POST)
        if form.is_valid():
            nihss = form.save(commit=False)
            nihss.patient = patient
            nihss.assessed_by = request.user
            nihss.save()
            
            # Calculate total score
            total_score = nihss.total_score
            
            # Create alert based on severity
            priority = 'medium'
            if total_score >= 21:
                priority = 'critical'
                message = f"CRITICAL: Severe stroke detected - NIHSS score {total_score}"
            elif total_score >= 16:
                priority = 'high'
                message = f"Moderate-to-severe stroke - NIHSS score {total_score}"
            elif total_score >= 5:
                priority = 'medium'
                message = f"Mild-to-moderate stroke - NIHSS score {total_score}"
            else:
                priority = 'low'
                message = f"Minor stroke - NIHSS score {total_score}"
            
            Alert.objects.create(
                patient=patient,
                priority=priority,
                alert_type='consultation',
                message=message
            )
            
            messages.success(request, 'NIHSS assessment recorded successfully!')
            return redirect('patient_detail', pk=patient_id)
    else:
        form = NIHSSAssessmentForm()
    
    return render(request, 'patients/nihss_form.html', {
        'form': form,
        'patient': patient
    })

# Consultation views
@login_required
@technician_or_admin_required
def consultation_request(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = ConsultationRequestForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = patient
            consultation.requested_by = request.user
            consultation.save()
            
            # Create alert for neurologists
            Alert.objects.create(
                patient=patient,
                consultation=consultation,
                priority='high',
                alert_type='consultation',
                message=f"New consultation request for {patient.first_name} {patient.last_name}"
            )
            
            messages.success(request, 'Consultation requested successfully!')
            return redirect('patient_detail', pk=patient_id)
    else:
        form = ConsultationRequestForm()
    
    return render(request, 'consultations/consultation_request.html', {
        'form': form,
        'patient': patient
    })

@login_required
def consultation_detail(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    patient = consultation.patient
    
    # Get the latest patient data for the neurologist
    latest_vitals = patient.vital_signs.order_by('-timestamp').first()
    latest_labs = patient.lab_results.order_by('-timestamp').first()
    latest_imaging = patient.imaging_studies.order_by('-timestamp').first()
    latest_nihss = patient.nihss_assessments.order_by('-timestamp').first()
    
    # Check if patient meets tPA criteria
    meets_criteria, exclusion_reasons = consultation.meets_tpa_criteria()
    
    context = {
        'consultation': consultation,
        'patient': patient,
        'latest_vitals': latest_vitals,
        'latest_labs': latest_labs,
        'latest_imaging': latest_imaging,
        'latest_nihss': latest_nihss,
        'meets_tpa_criteria': meets_criteria,
        'exclusion_reasons': exclusion_reasons
    }
    
    return render(request, 'consultations/consultation_detail.html', context)

# @login_required
# @neurologist_required
# def consultation_list(request):
#     # For neurologists, show pending consultations first, then completed ones
#     consultations = Consultation.objects.filter(
#         Q(status='requested') | Q(status='in_progress', neurologist=request.user) | Q(status='completed', neurologist=request.user)
#     ).order_by('status', '-requested_at')
    
#     return render(request, 'consultations/consultation_list.html', {
#         'consultations': consultations
#     })

# @login_required
# def consultation_list(request):
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        
        if user_role == 'neurologist':
            # Neurologists see pending consultations first, then their completed ones
            consultations = Consultation.objects.filter(
                Q(status='requested') | 
                Q(status='in_progress', neurologist=request.user) | 
                Q(status='completed', neurologist=request.user)
            ).order_by('status', '-requested_at')
            
        elif user_role == 'technician':
            # Technicians see consultations they've requested
            consultations = Consultation.objects.filter(
                requested_by=request.user
            ).order_by('-requested_at')
            
        elif user_role == 'admin':
            # Admins see all consultations
            consultations = Consultation.objects.all().order_by('-requested_at')
            
        else:
            consultations = Consultation.objects.none()
            messages.warning(request, "Your user role does not have permission to view consultations.")
            return redirect('home')
    else:
        consultations = Consultation.objects.none()
        messages.warning(request, "User profile not found. Please contact an administrator.")
        return redirect('home')
    
    return render(request, 'consultations/consultation_list.html', {
        'consultations': consultations,
        'user_role': user_role
    })

@login_required
def consultation_list(request):
    if hasattr(request.user, 'profile'):
        user_role = request.user.profile.role
        
        if user_role == 'neurologist':
            # Neurologists see pending consultations first, then their completed ones
            pending_consultations = Consultation.objects.filter(
                Q(status='requested') | 
                Q(status='in_progress', neurologist=request.user)
            ).order_by('-requested_at')
            
            completed_consultations = Consultation.objects.filter(
                status='completed', neurologist=request.user
            ).order_by('-completed_at')
            
        elif user_role == 'technician':
            # Technicians see consultations they've requested
            pending_consultations = Consultation.objects.filter(
                requested_by=request.user, status__in=['requested', 'in_progress']
            ).order_by('-requested_at')
            
            completed_consultations = Consultation.objects.filter(
                requested_by=request.user, status='completed'
            ).order_by('-completed_at')
            
        elif user_role == 'admin':
            # Admins see all consultations
            pending_consultations = Consultation.objects.filter(
                status__in=['requested', 'in_progress']
            ).order_by('-requested_at')
            
            completed_consultations = Consultation.objects.filter(
                status='completed'
            ).order_by('-completed_at')
            
        else:
            pending_consultations = Consultation.objects.none()
            completed_consultations = Consultation.objects.none()
            messages.warning(request, "Your user role does not have permission to view consultations.")
            return redirect('home')
    else:
        pending_consultations = Consultation.objects.none()
        completed_consultations = Consultation.objects.none()
        messages.warning(request, "User profile not found. Please contact an administrator.")
        return redirect('home')
    
    return render(request, 'consultations/consultation_list.html', {
        'pending_consultations': pending_consultations,
        'completed_consultations': completed_consultations,
        'user_role': user_role,
        'pending_count': pending_consultations.count()
    })


@login_required
@neurologist_required
def consultation_accept(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    
    if consultation.status == 'requested':
        consultation.status = 'in_progress'
        consultation.neurologist = request.user
        consultation.started_at = timezone.now()
        consultation.save()
        
        # Create alert for the technician
        Alert.objects.create(
            patient=consultation.patient,
            consultation=consultation,
            priority='medium',
            alert_type='consultation',
            message=f"Consultation accepted by Dr. {request.user.get_full_name() or request.user.username}"
        )
        
        messages.success(request, 'Consultation accepted!')
    else:
        messages.warning(request, 'This consultation has already been accepted.')
    
    return redirect('consultation_detail', pk=pk)

@login_required
@neurologist_required
def consultation_complete(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            updated_consultation = form.save(commit=False)
            updated_consultation.status = 'completed'
            updated_consultation.completed_at = timezone.now()
            updated_consultation.save()
            
            # Create alert about the completed consultation
            Alert.objects.create(
                patient=consultation.patient,
                consultation=consultation,
                priority='medium',
                alert_type='consultation',
                message=f"Consultation completed by Dr. {request.user.get_full_name() or request.user.username}"
            )
            
            # Create tPA alert if recommended
            if updated_consultation.tpa_recommended:
                Alert.objects.create(
                    patient=consultation.patient,
                    consultation=consultation,
                    priority='critical',
                    alert_type='tpa',
                    message=f"tPA treatment recommended by Dr. {request.user.get_full_name() or request.user.username}"
                )
            
            messages.success(request, 'Consultation completed!')
            return redirect('consultation_detail', pk=pk)
    else:
        form = ConsultationForm(instance=consultation)
    
    return render(request, 'consultations/consultation_complete.html', {
        'form': form,
        'consultation': consultation
    })

# Alert views
@login_required
def alert_list(request):
    alerts = Alert.objects.filter(acknowledged=False).order_by('-created_at', '-priority')
    
    return render(request, 'alerts/alert_list.html', {
        'alerts': alerts
    })

@login_required
def alert_acknowledge(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    
    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        messages.success(request, 'Alert acknowledged!')
    
    # Redirect back to referrer or alert list
    next_url = request.META.get('HTTP_REFERER', reverse('alert_list'))
    return redirect(next_url)

# Admin views
@login_required
@admin_required
def user_list(request):
    users = User.objects.all().order_by('username')
    return render(request, 'admin/user_list.html', {'users': users})

@login_required
@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.is_active = 'is_active' in request.POST
        user.save()
        
        # Update profile
        if hasattr(user, 'profile'):
            user.profile.role = request.POST.get('role')
            user.profile.phone = request.POST.get('phone')
            user.profile.save()
        else:
            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role'),
                phone=request.POST.get('phone')
            )
        
        messages.success(request, f'User {user.username} updated successfully!')
        return redirect('user_list')
    
    # Get profile or create context for new profile
    if hasattr(user, 'profile'):
        profile = user.profile
    else:
        profile = None
    
    return render(request, 'admin/user_edit.html', {'user_obj': user, 'profile': profile})


@login_required
def consultations_router(request):
    if hasattr(request.user, 'profile'):
        if request.user.profile.role == 'neurologist':
            return redirect('neurologist_consultations')
        elif request.user.profile.role == 'technician':
            return redirect('technician_consultations')
        elif request.user.profile.role == 'admin':
            return redirect('admin_consultations')
    # Default fallback
    messages.warning(request, "You don't have permission to view consultations.")
    return redirect('home')