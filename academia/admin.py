from django.contrib import admin
from .models import Member, Plan, Enrollment


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'joined_at')
    search_fields = ('first_name', 'last_name', 'email')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('member', 'plan', 'start_date', 'end_date')
    list_filter = ('plan',)
