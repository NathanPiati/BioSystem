from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import requests
import json
import base64
from io import BytesIO
from PIL import Image

from .models import AccessLog, Enrollment, Member, Plan
from personais.models import PersonalTrainer, PersonalClient, Workout
from django.db.models import Count


def search_zip_code(request):
    """Busca endereço por CEP usando ViaCEP API"""
    zip_code = request.GET.get('zip_code', '').replace(
        '-', '').replace('.', '')

    if not zip_code or len(zip_code) != 8:
        return JsonResponse({'error': 'CEP inválido'}, status=400)

    try:
        response = requests.get(
            f'https://viacep.com.br/ws/{zip_code}/json/', timeout=10)
        data = response.json()

        if 'erro' in data:
            return JsonResponse({'error': 'CEP não encontrado'}, status=404)

        address_data = {
            'street': data.get('logradouro', ''),
            'neighborhood': data.get('bairro', ''),
            'city': data.get('localidade', ''),
            'state': data.get('uf', ''),
        }

        return JsonResponse(address_data)

    except requests.RequestException:
        return JsonResponse({'error': 'Erro ao consultar CEP'}, status=500)


def home(request):
    # Dados básicos
    member_count = Member.objects.count()
    plan_count = Plan.objects.count()
    enrollment_count = Enrollment.objects.count()
    personal_count = PersonalTrainer.objects.count()
    client_count = PersonalClient.objects.count()
    workout_count = Workout.objects.count()

    # Dados para gráficos
    # 1. Alunos por Plano
    plans_data = Plan.objects.annotate(num_members=Count('enrollment')).values('name', 'num_members')
    plan_labels = [p['name'] for p in plans_data]
    plan_values = [p['num_members'] for p in plans_data]

    # 2. Acessos recentes (últimos 7 dias)
    seven_days_ago = timezone.now() - timezone.timedelta(days=7)
    access_data = AccessLog.objects.filter(timestamp__gte=seven_days_ago, success=True) \
        .extra(select={'day': "date(timestamp)"}) \
        .values('day') \
        .annotate(count=Count('id')) \
        .order_by('day')
    
    access_labels = [str(a['day']) for a in access_data]
    access_values = [a['count'] for a in access_data]

    # 3. Clientes por Personal
    personals_data = PersonalTrainer.objects.annotate(num_clients=Count('clients')).values('first_name', 'num_clients')
    personal_labels = [p['first_name'] for p in personals_data]
    personal_values = [p['num_clients'] for p in personals_data]

    context = {
        'title': 'Academia BioSystem',
        'description': 'Gestão de alunos, planos e matrículas para sua academia.',
        'member_count': member_count,
        'plan_count': plan_count,
        'enrollment_count': enrollment_count,
        'personal_count': personal_count,
        'client_count': client_count,
        'workout_count': workout_count,
        # Gráficos
        'plan_labels': json.dumps(plan_labels),
        'plan_values': json.dumps(plan_values),
        'access_labels': json.dumps(access_labels),
        'access_values': json.dumps(access_values),
        'personal_labels': json.dumps(personal_labels),
        'personal_values': json.dumps(personal_values),
    }
    return render(request, 'home.html', context)


class MemberListView(LoginRequiredMixin, ListView):
    model = Member
    template_name = 'academia/member_list.html'
    context_object_name = 'members'
    login_url = reverse_lazy('login')


class MemberCreateView(LoginRequiredMixin, CreateView):
    model = Member
    fields = ['first_name', 'last_name', 'email', 'phone', 'zip_code', 'street',
              'number', 'complement', 'neighborhood', 'city', 'state']
    template_name = 'academia/member_form.html'
    success_url = reverse_lazy('member_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Aluno {self.object.first_name} cadastrado com sucesso!')
        return response


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = Member
    fields = ['first_name', 'last_name', 'email', 'phone', 'zip_code', 'street',
              'number', 'complement', 'neighborhood', 'city', 'state']
    template_name = 'academia/member_form.html'
    success_url = reverse_lazy('member_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Aluno {self.object.first_name} atualizado com sucesso!')
        return response


def member_map(request):
    """Exibe um mapa com a localização dos alunos."""
    members = Member.objects.all()
    members_data = []

    for member in members:
        if not member.zip_code and member.full_address == 'Endereço não informado':
            continue

        query = None
        if member.zip_code:
            query = f'{member.zip_code}, Brasil'
        elif member.full_address != 'Endereço não informado':
            query = member.full_address

        if not query:
            continue

        members_data.append({
            'id': member.id,
            'name': str(member),
            'address': member.full_address,
            'query': query,
        })

    context = {
        'members': members_data,
        'title': 'Mapa de Alunos',
    }
    return render(request, 'academia/member_map.html', context)


class PlanListView(LoginRequiredMixin, ListView):
    model = Plan
    template_name = 'academia/plan_list.html'
    context_object_name = 'plans'
    login_url = reverse_lazy('login')


class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    fields = ['name', 'price', 'duration_days']
    template_name = 'academia/plan_form.html'
    success_url = reverse_lazy('plan_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Plano "{self.object.name}" criado com sucesso!')
        return response


class PlanUpdateView(LoginRequiredMixin, UpdateView):
    model = Plan
    fields = ['name', 'price', 'duration_days']
    template_name = 'academia/plan_form.html'
    success_url = reverse_lazy('plan_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Plano "{self.object.name}" atualizado com sucesso!')
        return response


class EnrollmentListView(LoginRequiredMixin, ListView):
    model = Enrollment
    template_name = 'academia/enrollment_list.html'
    context_object_name = 'enrollments'
    login_url = reverse_lazy('login')


class EnrollmentCreateView(LoginRequiredMixin, CreateView):
    model = Enrollment
    fields = ['member', 'plan', 'start_date', 'end_date']
    template_name = 'academia/enrollment_form.html'
    success_url = reverse_lazy('enrollment_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Matrícula de {self.object.member} criada com sucesso!')
        return response


class EnrollmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Enrollment
    fields = ['member', 'plan', 'start_date', 'end_date']
    template_name = 'academia/enrollment_form.html'
    success_url = reverse_lazy('enrollment_list')
    login_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f'Matrícula de {self.object.member} atualizada com sucesso!')
        return response


class AccessLogListView(LoginRequiredMixin, ListView):
    model = AccessLog
    template_name = 'academia/access_log_list.html'
    context_object_name = 'access_logs'
    paginate_by = 50
    login_url = reverse_lazy('login')

    def get_queryset(self):
        queryset = super().get_queryset()
        member_id = self.request.GET.get('member')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if member_id:
            queryset = queryset.filter(member_id=member_id)

        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['members'] = Member.objects.all()
        return context


# Funções utilitárias para biometria
def process_face_image(image_data):
    """
    Processa imagem facial e gera encoding
    image_data: base64 string da imagem
    """
    try:
        # Decodificar base64
        image_data = image_data.split(
            ',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        # Tentar importar face_recognition
        try:
            import face_recognition
            import numpy as np

            # Converter para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Converter para array numpy
            image_array = np.array(image)

            # Detectar faces
            face_locations = face_recognition.face_locations(image_array)
            if not face_locations:
                return {'error': 'Nenhuma face detectada na imagem'}

            # Gerar encoding da primeira face encontrada
            face_encodings = face_recognition.face_encodings(
                image_array, face_locations)
            if face_encodings:
                encoding = face_encodings[0]
                return {
                    'success': True,
                    'encoding': encoding.tolist(),
                    'confidence': 0.95  # Confiança padrão para detecção
                }
            else:
                return {'error': 'Não foi possível gerar encoding facial'}

        except ImportError:
            # Fallback: apenas validar que é uma imagem válida
            return {
                'success': True,
                'encoding': base64.b64encode(image_bytes).decode(),
                'confidence': 0.8,
                'note': 'face_recognition não instalado - usando fallback básico'
            }

    except Exception as e:
        return {'error': f'Erro ao processar imagem: {str(e)}'}


def compare_face_encodings(encoding1, encoding2, tolerance=0.6):
    """
    Compara dois encodings faciais
    """
    try:
        import face_recognition
        import numpy as np

        # Converter para numpy arrays
        enc1 = np.array(encoding1)
        enc2 = np.array(encoding2)

        # Calcular distância
        distance = face_recognition.face_distance([enc1], enc2)[0]

        # Calcular confiança baseada na distância
        confidence = max(0, 1 - distance)

        # Verificar se está dentro da tolerância
        match = distance <= tolerance

        return {
            'match': match,
            'confidence': confidence,
            'distance': distance
        }

    except ImportError:
        # Fallback básico
        return {
            'match': encoding1 == encoding2,
            'confidence': 0.5,
            'distance': 0.5,
            'note': 'face_recognition não instalado - comparação básica'
        }


# APIs Biométricas
@csrf_exempt
@require_http_methods(["POST"])
def enroll_fingerprint(request):
    """
    API para cadastrar impressão digital
    Parâmetros: member_id, fingerprint_data (base64)
    """
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        fingerprint_data = data.get('fingerprint_data')

        if not member_id or not fingerprint_data:
            return JsonResponse({
                'success': False,
                'message': 'member_id e fingerprint_data são obrigatórios'
            }, status=400)

        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Aluno não encontrado'
            }, status=404)

        # Decodificar dados da impressão digital
        try:
            fingerprint_bytes = base64.b64decode(fingerprint_data)
            member.fingerprint_template = fingerprint_bytes
            member.biometric_enabled = True
            member.save()

            return JsonResponse({
                'success': True,
                'message': 'Impressão digital cadastrada com sucesso'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erro ao processar dados biométricos: {str(e)}'
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def enroll_face(request):
    """
    API para cadastrar reconhecimento facial
    Parâmetros: member_id, face_image (base64)
    """
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        face_image = data.get('face_image')

        if not member_id or not face_image:
            return JsonResponse({
                'success': False,
                'message': 'member_id e face_image são obrigatórios'
            }, status=400)

        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Aluno não encontrado'
            }, status=404)

        # Processar imagem facial
        result = process_face_image(face_image)

        if 'error' in result:
            return JsonResponse({
                'success': False,
                'message': result['error']
            }, status=400)

        # Salvar encoding facial
        member.face_encoding = json.dumps(result['encoding'])
        member.biometric_enabled = True
        member.save()

        return JsonResponse({
            'success': True,
            'message': 'Face cadastrada com sucesso',
            'confidence': result.get('confidence', 0)
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def validate_fingerprint(request):
    """
    API para validar impressão digital
    Parâmetros: fingerprint_data (base64), turnstile_id (opcional)
    """
    try:
        data = json.loads(request.body)
        fingerprint_data = data.get('fingerprint_data')
        turnstile_id = data.get('turnstile_id', 'biometric_default')

        if not fingerprint_data:
            return JsonResponse({
                'success': False,
                'message': 'fingerprint_data é obrigatório'
            }, status=400)

        # Decodificar dados da impressão digital
        try:
            fingerprint_bytes = base64.b64decode(fingerprint_data)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Dados biométricos inválidos'
            }, status=400)

        # Buscar alunos com biometria ativada
        members_with_biometrics = Member.objects.filter(
            biometric_enabled=True,
            fingerprint_template__isnull=False
        )

        best_match = None
        best_confidence = 0

        for member in members_with_biometrics:
            # Comparação básica (em produção, use algoritmo específico)
            if member.fingerprint_template == fingerprint_bytes:
                best_match = member
                best_confidence = 0.95
                break

        if best_match and best_match.has_active_enrollment:
            # Acesso permitido
            AccessLog.objects.create(
                member=best_match,
                access_type='entry',
                success=True,
                auth_method='fingerprint',
                biometric_confidence=best_confidence,
                turnstile_id=turnstile_id
            )

            enrollment = best_match.active_enrollment
            return JsonResponse({
                'success': True,
                'message': 'Acesso permitido',
                'member': {
                    'id': best_match.id,
                    'name': str(best_match),
                    'plan': enrollment.plan.name if enrollment else 'N/A',
                    'enrollment_end': enrollment.end_date.isoformat() if enrollment else None
                },
                'confidence': best_confidence
            })

        # Acesso negado
        reason = "Impressão digital não reconhecida"
        if best_match and not best_match.has_active_enrollment:
            reason = "Matrícula expirada"

        AccessLog.objects.create(
            member=best_match,
            access_type='entry',
            success=False,
            reason=reason,
            auth_method='fingerprint',
            biometric_confidence=best_confidence if best_match else 0,
            turnstile_id=turnstile_id
        )

        return JsonResponse({
            'success': False,
            'message': reason
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def validate_face(request):
    """
    API para validar reconhecimento facial
    Parâmetros: face_image (base64), turnstile_id (opcional)
    """
    try:
        data = json.loads(request.body)
        face_image = data.get('face_image')
        turnstile_id = data.get('turnstile_id', 'biometric_default')

        if not face_image:
            return JsonResponse({
                'success': False,
                'message': 'face_image é obrigatório'
            }, status=400)

        # Processar imagem facial
        result = process_face_image(face_image)

        if 'error' in result:
            return JsonResponse({
                'success': False,
                'message': result['error']
            }, status=400)

        new_encoding = result['encoding']

        # Buscar alunos com biometria facial ativada
        members_with_face = Member.objects.filter(
            biometric_enabled=True,
            face_encoding__isnull=False
        )

        best_match = None
        best_confidence = 0

        for member in members_with_face:
            try:
                stored_encoding = json.loads(member.face_encoding)
                comparison = compare_face_encodings(
                    stored_encoding, new_encoding)

                if comparison['match'] and comparison['confidence'] > best_confidence:
                    best_match = member
                    best_confidence = comparison['confidence']

            except (json.JSONDecodeError, KeyError):
                continue

        if best_match and best_match.has_active_enrollment and best_confidence > 0.7:
            # Acesso permitido
            AccessLog.objects.create(
                member=best_match,
                access_type='entry',
                success=True,
                auth_method='face',
                biometric_confidence=best_confidence,
                turnstile_id=turnstile_id
            )

            enrollment = best_match.active_enrollment
            return JsonResponse({
                'success': True,
                'message': 'Acesso permitido',
                'member': {
                    'id': best_match.id,
                    'name': str(best_match),
                    'plan': enrollment.plan.name if enrollment else 'N/A',
                    'enrollment_end': enrollment.end_date.isoformat() if enrollment else None
                },
                'confidence': best_confidence
            })

        # Acesso negado
        reason = "Face não reconhecida"
        if best_match and not best_match.has_active_enrollment:
            reason = "Matrícula expirada"
        elif best_match and best_confidence <= 0.7:
            reason = f"Confiança insuficiente ({best_confidence:.2f})"

        AccessLog.objects.create(
            member=best_match,
            access_type='entry',
            success=False,
            reason=reason,
            auth_method='face',
            biometric_confidence=best_confidence if best_match else 0,
            turnstile_id=turnstile_id
        )

        return JsonResponse({
            'success': False,
            'message': reason,
            'confidence': best_confidence if best_match else 0
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)


# API para integração com catracas
def validate_access(request):
    """
    API para catracas validarem acesso
    Parâmetros: card_id (ID do cartão), turnstile_id (opcional)
    """
    card_id = request.GET.get('card_id')
    turnstile_id = request.GET.get('turnstile_id', 'default')

    if not card_id:
        return JsonResponse({
            'success': False,
            'message': 'ID do cartão não informado'
        }, status=400)

    try:
        member = Member.objects.get(card_id=card_id)
    except Member.DoesNotExist:
        # Registra tentativa de acesso com cartão inválido
        AccessLog.objects.create(
            member=None,  # Não temos member para associar
            access_type='entry',
            success=False,
            reason='Cartão não cadastrado',
            card_id=card_id,
            turnstile_id=turnstile_id
        )
        return JsonResponse({
            'success': False,
            'message': 'Cartão não cadastrado'
        })

    # Verifica se tem matrícula ativa
    if not member.has_active_enrollment:
        AccessLog.objects.create(
            member=member,
            access_type='entry',
            success=False,
            reason='Matrícula expirada ou inexistente',
            card_id=card_id,
            turnstile_id=turnstile_id
        )
        return JsonResponse({
            'success': False,
            'message': 'Matrícula expirada ou inexistente',
            'member': {
                'name': str(member),
                'enrollment_status': 'expired'
            }
        })

    # Acesso permitido
    AccessLog.objects.create(
        member=member,
        access_type='entry',
        success=True,
        card_id=card_id,
        turnstile_id=turnstile_id
    )

    enrollment = member.active_enrollment
    return JsonResponse({
        'success': True,
        'message': 'Acesso permitido',
        'member': {
            'id': member.id,
            'name': str(member),
            'plan': enrollment.plan.name if enrollment else 'N/A',
            'enrollment_end': enrollment.end_date.isoformat() if enrollment else None
        }
    })


def register_exit(request):
    """
    API para registrar saída da academia
    Parâmetros: card_id (ID do cartão), turnstile_id (opcional)
    """
    card_id = request.GET.get('card_id')
    turnstile_id = request.GET.get('turnstile_id', 'default')

    if not card_id:
        return JsonResponse({
            'success': False,
            'message': 'ID do cartão não informado'
        }, status=400)

    try:
        member = Member.objects.get(card_id=card_id)
    except Member.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cartão não encontrado'
        })

    # Registra saída
    AccessLog.objects.create(
        member=member,
        access_type='exit',
        success=True,
        card_id=card_id,
        turnstile_id=turnstile_id
    )

    return JsonResponse({
        'success': True,
        'message': 'Saída registrada',
        'member': {
            'name': str(member)
        }
    })


def get_access_logs(request):
    """
    API para consultar logs de acesso (para dashboard/admin)
    Parâmetros opcionais: member_id, date_from, date_to, limit
    """
    member_id = request.GET.get('member_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    limit = int(request.GET.get('limit', 100))

    logs = AccessLog.objects.all()

    if member_id:
        logs = logs.filter(member_id=member_id)

    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)

    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)

    logs = logs.order_by('-timestamp')[:limit]

    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'member_name': str(log.member) if log.member else 'N/A',
            'access_type': log.get_access_type_display(),
            'timestamp': log.timestamp.isoformat(),
            'success': log.success,
            'reason': log.reason,
            'card_id': log.card_id,
            'turnstile_id': log.turnstile_id
        })

    return JsonResponse({
        'success': True,
        'logs': data,
        'count': len(data)
    })
