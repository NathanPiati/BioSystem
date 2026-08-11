from django.db import models
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os


class Member(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='Nome')
    last_name = models.CharField(max_length=100, verbose_name='Sobrenome')
    email = models.EmailField(unique=True, verbose_name='E-mail')
    phone = models.CharField(max_length=20, blank=True,
                             verbose_name='Telefone')
    # Campo para identificação física (cartão RFID, código de barras, etc.)
    card_id = models.CharField(max_length=50, unique=True, blank=True, null=True,
                               verbose_name='ID do Cartão',
                               help_text='Código do cartão RFID ou código de barras')

    # Campos biométricos
    biometric_enabled = models.BooleanField(
        default=False, verbose_name='Biometria Ativada')
    fingerprint_template = models.BinaryField(blank=True, null=True,
                                              verbose_name='Template Digital',
                                              help_text='Dados biométricos da impressão digital')
    face_encoding = models.TextField(blank=True, verbose_name='Encoding Facial',
                                     help_text='Dados de reconhecimento facial (JSON)')
    face_photo = models.ImageField(upload_to='biometric_faces/', blank=True, null=True,
                                   verbose_name='Foto Facial',
                                   help_text='Foto para reconhecimento facial')

    # Campos de endereço
    zip_code = models.CharField(max_length=9, blank=True, verbose_name='CEP',
                                help_text='Formato: 00000-000')
    street = models.CharField(max_length=200, blank=True, verbose_name='Rua')
    number = models.CharField(max_length=10, blank=True, verbose_name='Número')
    complement = models.CharField(
        max_length=100, blank=True, verbose_name='Complemento')
    neighborhood = models.CharField(
        max_length=100, blank=True, verbose_name='Bairro')
    city = models.CharField(max_length=100, blank=True, verbose_name='Cidade')
    state = models.CharField(max_length=2, blank=True, verbose_name='Estado',
                             choices=[
                                 ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'),
                                 ('AM', 'Amazonas'), ('BA',
                                                      'Bahia'), ('CE', 'Ceará'),
                                 ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
                                 ('GO', 'Goiás'), ('MA',
                                                   'Maranhão'), ('MT', 'Mato Grosso'),
                                 ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
                                 ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
                                 ('PE', 'Pernambuco'), ('PI',
                                                        'Piauí'), ('RJ', 'Rio de Janeiro'),
                                 ('RN', 'Rio Grande do Norte'), ('RS',
                                                                 'Rio Grande do Sul'),
                                 ('RO', 'Rondônia'), ('RR',
                                                      'Roraima'), ('SC', 'Santa Catarina'),
                                 ('SP', 'São Paulo'), ('SE',
                                                       'Sergipe'), ('TO', 'Tocantins')
                             ])
    joined_at = models.DateField(
        auto_now_add=True, verbose_name='Data de entrada')

    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        """Retorna o endereço completo formatado"""
        address_parts = []
        if self.street:
            address_parts.append(f"{self.street}")
        if self.number:
            address_parts.append(f"{self.number}")
        if self.complement:
            address_parts.append(f"{self.complement}")
        if self.neighborhood:
            address_parts.append(f"{self.neighborhood}")
        if self.city and self.state:
            address_parts.append(f"{self.city}/{self.state}")
        if self.zip_code:
            address_parts.append(f"CEP: {self.zip_code}")

        return ", ".join(address_parts) if address_parts else "Endereço não informado"

    @property
    def has_active_enrollment(self):
        """Verifica se o aluno tem matrícula ativa"""
        today = timezone.now().date()
        return self.enrollment_set.filter(
            start_date__lte=today,
            end_date__gte=today
        ).exists()

    @property
    def active_enrollment(self):
        """Retorna a matrícula ativa do aluno"""
        today = timezone.now().date()
        return self.enrollment_set.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()

    @property
    def biometric_methods(self):
        """Retorna lista de métodos biométricos disponíveis"""
        methods = []
        if self.fingerprint_template:
            methods.append('fingerprint')
        if self.face_encoding:
            methods.append('face')
        return methods

    def save(self, *args, **kwargs):
        # Se a foto facial foi removida, limpar também o encoding
        if self.pk:  # Se já existe no banco
            old_instance = Member.objects.get(pk=self.pk)
            if old_instance.face_photo and not self.face_photo:
                # Foto foi removida, limpar encoding
                self.face_encoding = ''
                # Remover arquivo físico se existir
                if default_storage.exists(old_instance.face_photo.name):
                    default_storage.delete(old_instance.face_photo.name)
        super().save(*args, **kwargs)
        """Retorna o endereço completo formatado"""
        address_parts = []
        if self.street:
            address_parts.append(f"{self.street}")
        if self.number:
            address_parts.append(f"{self.number}")
        if self.complement:
            address_parts.append(f"{self.complement}")
        if self.neighborhood:
            address_parts.append(f"{self.neighborhood}")
        if self.city and self.state:
            address_parts.append(f"{self.city}/{self.state}")
        if self.zip_code:
            address_parts.append(f"CEP: {self.zip_code}")

        return ", ".join(address_parts) if address_parts else "Endereço não informado"

    @property
    def has_active_enrollment(self):
        """Verifica se o aluno tem matrícula ativa"""
        today = timezone.now().date()
        return self.enrollment_set.filter(
            start_date__lte=today,
            end_date__gte=today
        ).exists()

    @property
    def active_enrollment(self):
        """Retorna a matrícula ativa do aluno"""
        today = timezone.now().date()
        return self.enrollment_set.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()
        """Retorna o endereço completo formatado"""
        address_parts = []
        if self.street:
            address_parts.append(f"{self.street}")
        if self.number:
            address_parts.append(f"{self.number}")
        if self.complement:
            address_parts.append(f"{self.complement}")
        if self.neighborhood:
            address_parts.append(f"{self.neighborhood}")
        if self.city and self.state:
            address_parts.append(f"{self.city}/{self.state}")
        if self.zip_code:
            address_parts.append(f"CEP: {self.zip_code}")

        return ", ".join(address_parts) if address_parts else "Endereço não informado"


class Plan(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome do plano')
    price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name='Preço')
    duration_days = models.PositiveIntegerField(
        verbose_name='Duração (dias)',
        help_text='Validade do plano em dias')

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, verbose_name='Aluno')
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT, verbose_name='Plano')
    start_date = models.DateField(verbose_name='Data de início')
    end_date = models.DateField(verbose_name='Data de término')

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'

    def __str__(self):
        return f"{self.member} - {self.plan}"


class AccessLog(models.Model):
    """Log de acessos da catraca"""
    ACCESS_TYPES = [
        ('entry', 'Entrada'),
        ('exit', 'Saída'),
    ]

    AUTH_METHODS = [
        ('card', 'Cartão'),
        ('fingerprint', 'Impressão Digital'),
        ('face', 'Reconhecimento Facial'),
        ('card_biometric', 'Cartão + Biometria'),
    ]

    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, verbose_name='Aluno')
    access_type = models.CharField(
        max_length=5, choices=ACCESS_TYPES, verbose_name='Tipo de Acesso')
    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name='Data/Hora')
    success = models.BooleanField(
        default=True, verbose_name='Acesso Permitido')
    reason = models.CharField(max_length=200, blank=True,
                              verbose_name='Motivo da Negação',
                              help_text='Preenchido quando acesso é negado')
    card_id = models.CharField(
        max_length=50, verbose_name='ID do Cartão Usado')
    auth_method = models.CharField(max_length=20, choices=AUTH_METHODS, default='card',
                                   verbose_name='Método de Autenticação')
    biometric_confidence = models.FloatField(blank=True, null=True,
                                             verbose_name='Confiança Biométrica',
                                             help_text='Nível de confiança da validação biométrica (0-1)')
    turnstile_id = models.CharField(max_length=50, blank=True,
                                    verbose_name='ID da Catraca',
                                    help_text='Identificador da catraca física')

    class Meta:
        verbose_name = 'Log de Acesso'
        verbose_name_plural = 'Logs de Acesso'
        ordering = ['-timestamp']

    def __str__(self):
        status = "Permitido" if self.success else "Negado"
        return f"{self.member} - {self.access_type} - {status} ({self.timestamp})"
