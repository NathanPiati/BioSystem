from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from academia.models import Member
from billing.models import Subscription

from .forms import (AdminPersonalTrainerRegisterForm,
                    PersonalTrainerProfileForm, PersonalTrainerRegisterForm,
                    PersonalWhatsAppConfigForm,
                    WorkoutExerciseFormSet, WorkoutForm)
from .models import (Exercise, PersonalClient, PersonalTrainer,
                     PersonalWhatsAppConfig, Workout, WorkoutExercise)
from .services import EvolutionAPIError, send_workout_message


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_personal(user):
    """Retorna o PersonalTrainer do usuário logado, ou None para staff/superuser."""
    if user.is_staff or user.is_superuser:
        return None

    try:
        return user.personaltrainer
    except PersonalTrainer.DoesNotExist:
        return None


def _has_active_subscription(personal):
    if personal is None:
        return False
    if personal.subscription_exempt:
        return True
    try:
        return personal.subscription.has_access()
    except Subscription.DoesNotExist:
        return False


def _redirect_without_personal(request):
    messages.error(
        request,
        'Você não tem acesso a esta área. Sua conta não está vinculada a '
        'um acesso administrativo.',
    )
    return redirect('home')


class PersonalScopedMixin(LoginRequiredMixin):
    """
    Define self.personal = PersonalTrainer do usuário logado.
    Staff/superuser recebe self.personal = None (vê tudo).
    Usuário sem vínculo é redirecionado.
    """
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.personal = _get_personal(request.user)
        if not (request.user.is_staff or request.user.is_superuser) and self.personal is None:
            messages.error(
                request, 'Sua conta não está vinculada a nenhum personal trainer.')
            return redirect('home')
        if not (request.user.is_staff or request.user.is_superuser) and not _has_active_subscription(self.personal):
            messages.info(
                request, 'Ative sua assinatura para acessar o Portal Personal Trainer.')
            return redirect('subscription_checkout')
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy('login')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                'Você não tem permissão para acessar esta área.',
            )
            return redirect('home')
        return super().handle_no_permission()


class PortalLoginView(LoginView):
    """Envia personais ao portal e usuarios da academia para a academia."""

    template_name = 'registration/login.html'

    def get_success_url(self):
        if _get_personal(self.request.user) is not None:
            if not _has_active_subscription(_get_personal(self.request.user)):
                return reverse('subscription_checkout')
            return reverse('portal_home')
        return super().get_success_url()

    def get_default_redirect_url(self):
        if _get_personal(self.request.user) is not None:
            if not _has_active_subscription(_get_personal(self.request.user)):
                return reverse('subscription_checkout')
            return reverse('portal_home')
        return reverse('home')


class SuperuserRequiredMixin(StaffRequiredMixin):
    def test_func(self):
        return self.request.user.is_superuser


class WhatsAppConfigListView(SuperuserRequiredMixin, ListView):
    model = PersonalWhatsAppConfig
    template_name = 'personais/whatsapp_config_list.html'
    context_object_name = 'configs'

    def get_queryset(self):
        return self.model.objects.select_related('personal')


class WhatsAppConfigCreateView(SuperuserRequiredMixin, CreateView):
    model = PersonalWhatsAppConfig
    form_class = PersonalWhatsAppConfigForm
    template_name = 'personais/whatsapp_config_form.html'
    success_url = reverse_lazy('whatsapp_config_list')

    def form_valid(self, form):
        messages.success(self.request, 'Configuração de WhatsApp salva.')
        return super().form_valid(form)


class WhatsAppConfigUpdateView(SuperuserRequiredMixin, UpdateView):
    model = PersonalWhatsAppConfig
    form_class = PersonalWhatsAppConfigForm
    template_name = 'personais/whatsapp_config_form.html'
    success_url = reverse_lazy('whatsapp_config_list')

    def form_valid(self, form):
        messages.success(self.request, 'Configuração de WhatsApp atualizada.')
        return super().form_valid(form)


# ── Portal home ────────────────────────────────────────────────────────────────

@login_required(login_url='login')
def portal_home(request):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        return render(request, 'portal/dashboard.html', {'title': 'Portal PT', 'no_access': True})
    if personal and not _has_active_subscription(personal):
        return render(request, 'portal/dashboard.html', {
            'title': 'Assinatura necessária',
            'subscription_required': True,
        })

    if personal:
        base_clients = PersonalClient.objects.filter(personal=personal)
        base_workouts = Workout.objects.filter(personal=personal)
        base_pt = PersonalTrainer.objects.filter(pk=personal.pk)
    else:
        base_clients = PersonalClient.objects.all()
        base_workouts = Workout.objects.all()
        base_pt = PersonalTrainer.objects.filter(is_active=True)

    context = {
        'title': 'Portal Personal Trainer',
        'personal': personal,
        'total_personals':  base_pt.count(),
        'total_clients':    base_clients.count(),
        'total_workouts':   base_workouts.count(),
        'total_exercises':  WorkoutExercise.objects.filter(workout__in=base_workouts).count(),
        'clients_without_workout': base_clients.filter(workouts__isnull=True).count(),
        'recent_personals': base_pt.prefetch_related('clients')[:5],
        'recent_workouts':  base_workouts.select_related('client', 'personal').order_by('-updated_at')[:6],
        'recent_clients':   base_clients.select_related('personal').prefetch_related('workouts').order_by('-created_at')[:6],
    }
    return render(request, 'portal/dashboard.html', context)


# ── Auto-cadastro de personal ──────────────────────────────────────────────────

def portal_register(request):
    # Usuário logado e já tem personal → vai direto para o portal
    if request.user.is_authenticated and _get_personal(request.user) is not None:
        personal = _get_personal(request.user)
        if _has_active_subscription(personal):
            return redirect('portal_home')
        return redirect('subscription_checkout')

    # Usuário logado SEM personal → só preenche dados de personal (sem criar novo User)
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = PersonalTrainerProfileForm(request.POST)
            if form.is_valid():
                personal = form.save(request.user)
                messages.success(
                    request, f'Perfil criado! Bem-vindo, {personal.first_name}.')
                return redirect('subscription_checkout')
        else:
            form = PersonalTrainerProfileForm()
        return render(request, 'portal/registro.html', {
            'form': form, 'title': 'Completar perfil — Portal PT', 'profile_only': True,
        })

    # Usuário não autenticado → cria User + PersonalTrainer
    if request.method == 'POST':
        form = AdminPersonalTrainerRegisterForm(request.POST)
        if form.is_valid():
            personal = form.save()
            login(request, personal.user)
            messages.success(
                request, f'Bem-vindo, {personal.first_name}! Conta criada com sucesso.')
            return redirect('subscription_checkout')
    else:
        form = AdminPersonalTrainerRegisterForm()
    return render(request, 'portal/registro.html', {'form': form, 'title': 'Criar conta — Portal PT'})


# ── PersonalTrainer views ──────────────────────────────────────────────────────

class PersonalTrainerListView(StaffRequiredMixin, ListView):
    model = PersonalTrainer
    template_name = 'personais/personal_list.html'
    context_object_name = 'personals'


@login_required(login_url='login')
def personal_create(request):
    """Staff cria um personal junto com a conta de acesso."""
    if not (request.user.is_staff or request.user.is_superuser):
        return _redirect_without_personal(request)
    if request.method == 'POST':
        form = PersonalTrainerRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal cadastrado com sucesso.')
            return redirect('personal_list')
    else:
        form = PersonalTrainerRegisterForm()
    return render(request, 'personais/personal_form.html', {'form': form, 'title': 'Novo personal'})


class PersonalTrainerUpdateView(PersonalScopedMixin, UpdateView):
    model = PersonalTrainer
    fields = ['first_name', 'last_name', 'email',
              'cpf', 'phone', 'cref', 'is_active', 'subscription_exempt']
    template_name = 'personais/personal_form.html'

    def get_success_url(self):
        return reverse_lazy('personal_detail', kwargs={'pk': self.object.pk})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.personal and obj != self.personal:
            raise Http404
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Dados atualizados com sucesso.')
        return super().form_valid(form)


class PersonalTrainerDetailView(PersonalScopedMixin, DetailView):
    model = PersonalTrainer
    template_name = 'personais/personal_detail.html'
    context_object_name = 'personal'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.personal and obj != self.personal:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = self.object.clients.prefetch_related(
            'workouts').order_by('first_name')
        context['total_workouts'] = Workout.objects.filter(
            personal=self.object).count()
        return context


class PersonalTrainerDeleteView(StaffRequiredMixin, DeleteView):
    model = PersonalTrainer
    template_name = 'personais/personal_confirm_delete.html'
    success_url = reverse_lazy('personal_list')

    def form_valid(self, form):
        messages.success(self.request, 'Personal excluído com sucesso.')
        return super().form_valid(form)


# ── PersonalClient views ───────────────────────────────────────────────────────

class PersonalClientListView(PersonalScopedMixin, ListView):
    model = PersonalClient
    template_name = 'personais/client_list.html'
    context_object_name = 'clients'

    def get_queryset(self):
        qs = PersonalClient.objects.select_related(
            'personal', 'academy_member')
        search = self.request.GET.get('q', '').strip()
        academy = self.request.GET.get('academy', '').strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(goal__icontains=search)
            )
        if academy == 'yes':
            qs = qs.filter(academy_member__isnull=False)
        elif academy == 'no':
            qs = qs.filter(academy_member__isnull=True)
        if self.personal:
            return qs.filter(personal=self.personal)
        personal_id = self.request.GET.get('personal')
        if personal_id:
            qs = qs.filter(personal_id=personal_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.personal:
            context['personals'] = PersonalTrainer.objects.filter(
                is_active=True)
        return context


@login_required(login_url='login')
def personal_client_create(request):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        messages.error(
            request, 'Sua conta não está vinculada a nenhum personal trainer.')
        return redirect('home')

    fields = ['first_name', 'last_name', 'email',
              'phone', 'goal', 'observations', 'born_at']
    if not personal:
        fields = ['personal'] + fields
    FormClass = modelform_factory(PersonalClient, fields=fields)

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            if personal:
                client.personal = personal
            client.save()
            messages.success(request, 'Cliente cadastrado com sucesso.')
            return redirect('personal_client_list')
    else:
        form = FormClass()

    return render(request, 'personais/client_form.html', {'form': form, 'title': 'Novo cliente'})


@login_required(login_url='login')
def personal_client_edit(request, pk):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        messages.error(
            request, 'Sua conta não está vinculada a nenhum personal trainer.')
        return redirect('home')

    client = get_object_or_404(PersonalClient, pk=pk)
    if personal and client.personal != personal:
        raise Http404

    fields = ['first_name', 'last_name', 'email',
              'phone', 'goal', 'observations', 'born_at']
    if not personal:
        fields = ['personal'] + fields
    FormClass = modelform_factory(PersonalClient, fields=fields)

    if request.method == 'POST':
        form = FormClass(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso.')
            return redirect('personal_client_list')
    else:
        form = FormClass(instance=client)

    return render(request, 'personais/client_form.html', {
        'form': form, 'title': 'Editar cliente', 'object': client,
    })


class PersonalClientDetailView(PersonalScopedMixin, DetailView):
    model = PersonalClient
    template_name = 'personais/client_detail.html'
    context_object_name = 'client'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.personal and obj.personal != self.personal:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workouts'] = self.object.workouts.prefetch_related(
            'exercises').order_by('-updated_at')
        return context


class PersonalClientDeleteView(PersonalScopedMixin, DeleteView):
    model = PersonalClient
    template_name = 'personais/client_confirm_delete.html'
    success_url = reverse_lazy('personal_client_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.personal and obj.personal != self.personal:
            raise Http404
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Cliente excluído com sucesso.')
        return super().form_valid(form)


@login_required(login_url='login')
def move_client_to_academy(request, pk):
    personal = _get_personal(request.user)
    client = get_object_or_404(PersonalClient, pk=pk)
    if personal and client.personal != personal:
        raise Http404
    if client.academy_member:
        messages.info(request, 'Este cliente já foi enviado para a academia.')
        return redirect('personal_client_list')
    member = Member.objects.create(
        first_name=client.first_name,
        last_name=client.last_name,
        email=client.email or f'cliente{client.id}@sememail.local',
        phone=client.phone,
    )
    client.academy_member = member
    client.save(update_fields=['academy_member'])
    messages.success(
        request, f'Cliente {client} enviado para academia como aluno.')
    return redirect('personal_client_list')


# ── Workout views ──────────────────────────────────────────────────────────────

class WorkoutListView(PersonalScopedMixin, ListView):
    model = Workout
    template_name = 'personais/workout_list.html'
    context_object_name = 'workouts'

    def get_queryset(self):
        qs = Workout.objects.select_related('personal', 'client')
        search = self.request.GET.get('q', '').strip()
        personal_id = self.request.GET.get('personal')
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(goal__icontains=search)
                | Q(client__first_name__icontains=search)
                | Q(client__last_name__icontains=search)
            )
        if self.personal:
            return qs.filter(personal=self.personal)
        if personal_id:
            qs = qs.filter(personal_id=personal_id)
        client_id = self.request.GET.get('client')
        if client_id:
            qs = qs.filter(client_id=client_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.personal:
            context['clients'] = PersonalClient.objects.filter(
                personal=self.personal)
        else:
            context['clients'] = PersonalClient.objects.select_related(
                'personal')
            context['personals'] = PersonalTrainer.objects.filter(
                is_active=True)
        return context


@login_required(login_url='login')
def workout_create(request):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        messages.error(
            request, 'Sua conta não está vinculada a nenhum personal trainer.')
        return redirect('home')
    if request.method == 'POST':
        form = WorkoutForm(request.POST, personal=personal)
        formset = WorkoutExerciseFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            workout = form.save()
            formset.instance = workout
            formset.save()
            messages.success(request, 'Treino cadastrado com sucesso.')
            return redirect('workout_list')
    else:
        form = WorkoutForm(personal=personal)
        formset = WorkoutExerciseFormSet()
    return render(request, 'personais/workout_form.html', {
        'form': form, 'formset': formset, 'title': 'Novo treino',        'exercises': Exercise.objects.filter(is_active=True).order_by('name'), })


@login_required(login_url='login')
def workout_edit(request, pk):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        messages.error(
            request, 'Sua conta não está vinculada a nenhum personal trainer.')
        return redirect('home')
    workout = get_object_or_404(Workout, pk=pk)
    if personal and workout.personal != personal:
        raise Http404
    if request.method == 'POST':
        form = WorkoutForm(request.POST, instance=workout, personal=personal)
        formset = WorkoutExerciseFormSet(request.POST, instance=workout)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Treino atualizado com sucesso.')
            return redirect('workout_list')
    else:
        form = WorkoutForm(instance=workout, personal=personal)
        formset = WorkoutExerciseFormSet(instance=workout)
    return render(request, 'personais/workout_form.html', {
        'form': form, 'formset': formset, 'title': 'Editar treino',        'exercises': Exercise.objects.filter(is_active=True).order_by('name'), })


class WorkoutDetailView(PersonalScopedMixin, DetailView):
    model = Workout
    template_name = 'personais/workout_detail.html'
    context_object_name = 'workout'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.personal and obj.personal != self.personal:
            raise Http404
        return obj


@login_required(login_url='login')
def workout_print(request, pk):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        messages.error(
            request, 'Sua conta não está vinculada a nenhum personal trainer.')
        return redirect('home')

    workout = get_object_or_404(
        Workout.objects.select_related(
            'client', 'personal').prefetch_related('exercises'),
        pk=pk,
    )
    if personal and workout.personal != personal:
        raise Http404

    return render(request, 'personais/workout_print.html', {'workout': workout})


@login_required(login_url='login')
def workout_send_whatsapp(request, pk):
    if request.method != 'POST':
        raise Http404

    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        messages.error(
            request, 'Sua conta não está vinculada a nenhum personal trainer.')
        return redirect('home')

    workout = get_object_or_404(
        Workout.objects.select_related(
            'client', 'personal').prefetch_related('exercises'),
        pk=pk,
    )
    if personal and workout.personal != personal:
        raise Http404

    try:
        send_workout_message(workout)
    except EvolutionAPIError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request, f'Ficha enviada para {workout.client.first_name} pelo WhatsApp.')
    return redirect('workout_detail', pk=workout.pk)


class WorkoutDeleteView(PersonalScopedMixin, DeleteView):
    model = Workout
    template_name = 'personais/workout_confirm_delete.html'
    success_url = reverse_lazy('workout_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if self.personal and obj.personal != self.personal:
            raise Http404
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Treino excluído com sucesso.')
        return super().form_valid(form)


# ── Exercise library views ─────────────────────────────────────────────────────

class ExerciseListView(PersonalScopedMixin, ListView):
    model = Exercise
    template_name = 'personais/exercise_list.html'
    context_object_name = 'exercises'

    def get_queryset(self):
        qs = Exercise.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
        group = self.request.GET.get('group', '').strip()
        if group:
            qs = qs.filter(muscle_group=group)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['muscle_groups'] = Exercise.MUSCLE_GROUP_CHOICES
        return context


@login_required(login_url='login')
def exercise_create(request):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        return _redirect_without_personal(request)
    FormClass = modelform_factory(
        Exercise, fields=['name', 'muscle_group', 'description', 'is_active'])
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercício cadastrado com sucesso.')
            return redirect('exercise_list')
    else:
        form = FormClass()
    return render(request, 'personais/exercise_form.html', {'form': form, 'title': 'Novo exercício'})


@login_required(login_url='login')
def exercise_edit(request, pk):
    personal = _get_personal(request.user)
    if not (request.user.is_staff or request.user.is_superuser) and personal is None:
        return _redirect_without_personal(request)
    exercise = get_object_or_404(Exercise, pk=pk)
    FormClass = modelform_factory(
        Exercise, fields=['name', 'muscle_group', 'description', 'is_active'])
    if request.method == 'POST':
        form = FormClass(request.POST, instance=exercise)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercício atualizado com sucesso.')
            return redirect('exercise_list')
    else:
        form = FormClass(instance=exercise)
    return render(request, 'personais/exercise_form.html', {
        'form': form, 'title': 'Editar exercício', 'object': exercise,
    })


class ExerciseDeleteView(PersonalScopedMixin, DeleteView):
    model = Exercise
    template_name = 'personais/exercise_confirm_delete.html'
    success_url = reverse_lazy('exercise_list')

    def form_valid(self, form):
        messages.success(self.request, 'Exercício excluído com sucesso.')
        return super().form_valid(form)
