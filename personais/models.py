from django.conf import settings
from django.db.models import Q
from django.db import models

from academia.models import Member


class Exercise(models.Model):
    MUSCLE_GROUP_CHOICES = [
        ('peito',      'Peito'),
        ('costas',     'Costas'),
        ('ombros',     'Ombros'),
        ('biceps',     'Bíceps'),
        ('triceps',    'Tríceps'),
        ('antebraco',  'Antebraço'),
        ('abdomen',    'Abdômen'),
        ('gluteo',     'Glúteo'),
        ('quadriceps', 'Quadríceps'),
        ('posterior',  'Posterior de coxa'),
        ('panturrilha', 'Panturrilha'),
        ('full_body',  'Full body'),
        ('cardio',     'Cardio'),
        ('outro',      'Outro'),
    ]

    name = models.CharField(max_length=120, unique=True, verbose_name='Nome')
    muscle_group = models.CharField(
        max_length=30, blank=True, choices=MUSCLE_GROUP_CHOICES, verbose_name='Grupo muscular')
    description = models.TextField(blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exercício'
        verbose_name_plural = 'Exercícios'
        ordering = ['name']

    def __str__(self):
        return self.name


class PersonalTrainer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='personaltrainer',
        verbose_name='Usuário',
    )
    first_name = models.CharField(max_length=100, verbose_name='Nome')
    last_name = models.CharField(
        max_length=100, blank=True, verbose_name='Sobrenome')
    email = models.EmailField(unique=True, verbose_name='E-mail')
    cpf = models.CharField(max_length=11, blank=True, verbose_name='CPF')
    subscription_exempt = models.BooleanField(
        default=False,
        verbose_name='Isento de assinatura',
        help_text='Permite acesso sem cobrança mensal. Use apenas para contas criadas pelo administrador.',
    )
    phone = models.CharField(max_length=20, blank=True,
                             verbose_name='Telefone')
    cref = models.CharField(max_length=30, blank=True, verbose_name='CREF')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Personal'
        verbose_name_plural = 'Personais'
        ordering = ['first_name', 'last_name']
        constraints = [
            models.UniqueConstraint(
                fields=['cpf'],
                condition=Q(cpf__gt=''),
                name='unique_personal_trainer_cpf',
            ),
        ]

    def __str__(self):
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email


class PersonalClient(models.Model):
    personal = models.ForeignKey(
        PersonalTrainer,
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name='Personal',
    )
    first_name = models.CharField(max_length=100, verbose_name='Nome')
    last_name = models.CharField(
        max_length=100, blank=True, verbose_name='Sobrenome')
    email = models.EmailField(blank=True, verbose_name='E-mail')
    phone = models.CharField(max_length=20, blank=True,
                             verbose_name='Telefone')
    goal = models.CharField(max_length=200, blank=True,
                            verbose_name='Objetivo')
    observations = models.TextField(blank=True, verbose_name='Observacoes')
    born_at = models.DateField(
        null=True, blank=True, verbose_name='Data de nascimento')
    academy_member = models.OneToOneField(
        Member,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='personal_origin',
        verbose_name='Aluno na academia',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cliente do personal'
        verbose_name_plural = 'Clientes dos personais'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'.strip()


class Workout(models.Model):
    personal = models.ForeignKey(
        PersonalTrainer,
        on_delete=models.CASCADE,
        related_name='workouts',
        verbose_name='Personal',
    )
    client = models.ForeignKey(
        PersonalClient,
        on_delete=models.CASCADE,
        related_name='workouts',
        verbose_name='Cliente',
    )
    name = models.CharField(max_length=120, verbose_name='Nome do treino')
    goal = models.CharField(max_length=200, blank=True,
                            verbose_name='Objetivo')
    notes = models.TextField(blank=True, verbose_name='Observacoes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Treino'
        verbose_name_plural = 'Treinos'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.name} - {self.client}'

    def save(self, *args, **kwargs):
        # Mantem o treino sempre vinculado ao mesmo personal do cliente.
        self.personal = self.client.personal
        super().save(*args, **kwargs)


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(
        Workout,
        on_delete=models.CASCADE,
        related_name='exercises',
        verbose_name='Treino',
    )
    name = models.CharField(max_length=120, verbose_name='Exercicio')
    sets = models.PositiveIntegerField(default=3, verbose_name='Series')
    reps = models.CharField(max_length=50, verbose_name='Repeticoes')
    load = models.CharField(max_length=50, blank=True, verbose_name='Carga')
    rest_seconds = models.PositiveIntegerField(
        default=60, verbose_name='Descanso (segundos)')
    order = models.PositiveIntegerField(default=1, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Exercicio do treino'
        verbose_name_plural = 'Exercicios do treino'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.name} ({self.workout.name})'
