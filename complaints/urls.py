from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('report/', views.report_fraud, name='report_fraud'),
    path('track/', views.track_status, name='track_status'),
    path('investigator/dashboard/', views.investigator_dashboard, name='investigator_dashboard'),
    path('investigator/case/<str:tracking_id>/', views.case_detail, name='case_detail'),
    path('investigator/victim/<int:user_id>/', views.victim_profile, name='victim_profile'),
    path('investigator/update/<str:tracking_id>/', views.update_case_status, name='update_case_status'),
    path('dashboard/', views.victim_dashboard, name='victim_dashboard'),
    path('dashboard/<str:tracking_id>/evidence/', views.add_evidence, name='add_evidence'),
    path('evidence/<int:evidence_id>/preview/', views.preview_evidence, name='preview_evidence'),
    path('investigator/login/', views.investigator_login, name='investigator_login'),
]
