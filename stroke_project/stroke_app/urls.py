from django.urls import path
from . import views

urlpatterns = [
    # Home and dashboard
    path('', views.home, name='home'),
    path('debug/', views.debug_view, name='debug'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('profile-setup/', views.profile_setup, name='profile_setup'),
    
    # Patient views
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_create, name='patient_create'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    
    # Vital Signs
    path('patients/<int:patient_id>/vitals/add/', views.vitals_create, name='vitals_create'),
    
    # Lab Results
    path('patients/<int:patient_id>/lab-results/add/', views.lab_results_create, name='lab_results_create'),
    
    # Imaging Studies
    path('patients/<int:patient_id>/imaging/add/', views.imaging_study_create, name='imaging_study_create'),
    
    # NIHSS Assessments
    path('patients/<int:patient_id>/nihss/add/', views.nihss_assessment_create, name='nihss_assessment_create'),
    
    # Consultations
    path('patients/<int:patient_id>/consultation/request/', views.consultation_request, name='consultation_request'),
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('consultations/<int:pk>/accept/', views.consultation_accept, name='consultation_accept'),
    path('consultations/<int:pk>/complete/', views.consultation_complete, name='consultation_complete'),
    
    # Alerts
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/<int:pk>/acknowledge/', views.alert_acknowledge, name='alert_acknowledge'),
    
    # Admin views
    # path('admin/users/', views.user_list, name='user_list'),
    # path('admin/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    # Admin views
    path('custom-admin/users/', views.user_list, name='user_list'),
    path('custom-admin/users/<int:pk>/edit/', views.user_edit, name='user_edit'),
]