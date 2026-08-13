from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('api/search-zip-code/', views.search_zip_code, name='search_zip_code'),

    path('members/', views.MemberListView.as_view(), name='member_list'),
    path('members/new/', views.MemberCreateView.as_view(), name='member_create'),
    path('members/<int:pk>/edit/',
         views.MemberUpdateView.as_view(), name='member_edit'),
    path('members/map/', views.member_map, name='member_map'),

    path('plans/', views.PlanListView.as_view(), name='plan_list'),
    path('plans/new/', views.PlanCreateView.as_view(), name='plan_create'),
    path('plans/<int:pk>/edit/', views.PlanUpdateView.as_view(), name='plan_edit'),

    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment_list'),
    path('enrollments/new/', views.EnrollmentCreateView.as_view(),
         name='enrollment_create'),
    path('enrollments/<int:pk>/edit/',
         views.EnrollmentUpdateView.as_view(), name='enrollment_edit'),

    path('access-logs/', views.AccessLogListView.as_view(), name='access_log_list'),

    # APIs para catracas
    path('api/turnstile/validate-access/',
         views.validate_access, name='validate_access'),
    path('api/turnstile/register-exit/',
         views.register_exit, name='register_exit'),
    path('api/turnstile/access-logs/', views.get_access_logs, name='access_logs'),

    # APIs Biométricas
    path('api/biometric/enroll-fingerprint/',
         views.enroll_fingerprint, name='enroll_fingerprint'),
    path('api/biometric/enroll-face/', views.enroll_face, name='enroll_face'),
    path('api/biometric/validate-fingerprint/',
         views.validate_fingerprint, name='validate_fingerprint'),
    path('api/biometric/validate-face/',
         views.validate_face, name='validate_face'),
]
