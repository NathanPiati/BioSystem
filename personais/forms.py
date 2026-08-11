from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.forms import inlineformset_factory

from .models import PersonalClient, PersonalTrainer, Workout, WorkoutExercise


class WorkoutForm(forms.ModelForm):
    class Meta:
        model = Workout
        fields = ['client', 'name', 'goal', 'notes']

    def __init__(self, *args, personal=None, **kwargs):
        super().__init__(*args, **kwargs)
        if personal is not None:
            self.fields['client'].queryset = PersonalClient.objects.filter(
                personal=personal)


class PersonalTrainerRegisterForm(forms.Form):
    """Cria um User + PersonalTrainer de uma vez só."""
    first_name = forms.CharField(max_length=100, label='Nome')
    last_name = forms.CharField(
        max_length=100, required=False, label='Sobrenome')
    email = forms.EmailField(label='E-mail')
    phone = forms.CharField(max_length=20, required=False, label='Telefone')
    cref = forms.CharField(max_length=30, required=False, label='CREF')
    username = forms.CharField(max_length=150, label='Nome de usuário')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, label='Confirmar senha')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if PersonalTrainer.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        pw2 = cleaned_data.get('password_confirm')
        if pw and pw2 and pw != pw2:
            self.add_error('password_confirm', 'As senhas não coincidem.')
        if pw:
            try:
                validate_password(pw)
            except Exception as exc:
                for msg in exc.messages:
                    self.add_error('password', msg)
        return cleaned_data

    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(
            username=d['username'],
            email=d['email'],
            password=d['password'],
            first_name=d['first_name'],
            last_name=d.get('last_name', ''),
        )
        personal = PersonalTrainer.objects.create(
            user=user,
            first_name=d['first_name'],
            last_name=d.get('last_name', ''),
            email=d['email'],
            phone=d.get('phone', ''),
            cref=d.get('cref', ''),
        )
        return personal


class PersonalTrainerProfileForm(forms.Form):
    """Para usuários já logados que ainda não têm perfil de personal."""
    first_name = forms.CharField(max_length=100, label='Nome')
    last_name = forms.CharField(
        max_length=100, required=False, label='Sobrenome')
    email = forms.EmailField(label='E-mail')
    phone = forms.CharField(max_length=20, required=False, label='Telefone')
    cref = forms.CharField(max_length=30, required=False, label='CREF')

    def clean_email(self):
        email = self.cleaned_data['email']
        if PersonalTrainer.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, user):
        d = self.cleaned_data
        personal = PersonalTrainer.objects.create(
            user=user,
            first_name=d['first_name'],
            last_name=d.get('last_name', ''),
            email=d['email'],
            phone=d.get('phone', ''),
            cref=d.get('cref', ''),
        )
        return personal


WorkoutExerciseFormSet = inlineformset_factory(
    Workout,
    WorkoutExercise,
    fields=['order', 'name', 'sets', 'reps', 'load', 'rest_seconds'],
    extra=1,
    can_delete=True,
)
