from django.contrib import admin

from .models import PersonalClient, PersonalTrainer, Workout, WorkoutExercise


class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 1


@admin.register(PersonalTrainer)
class PersonalTrainerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'is_active')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('is_active',)


@admin.register(PersonalClient)
class PersonalClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'personal', 'phone', 'academy_member')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('personal',)


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'personal', 'client', 'updated_at')
    search_fields = ('name', 'client__first_name', 'client__last_name')
    list_filter = ('personal',)
    inlines = [WorkoutExerciseInline]
