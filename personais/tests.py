from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from .forms import WorkoutExerciseFormSet
from .models import PersonalClient, PersonalTrainer, Workout
from .services import EvolutionAPIError, build_workout_message, send_workout_message


class EvolutionServiceTests(SimpleTestCase):
    def _workout(self, phone='(11) 99999-8888'):
        client = SimpleNamespace(phone=phone, __str__=lambda self: 'Ana Silva')
        personal = SimpleNamespace(__str__=lambda self: 'Carlos Personal')
        exercise = SimpleNamespace(
            order=1,
            name='Agachamento',
            sets=4,
            reps='12',
            load='20 kg',
            rest_seconds=60,
        )
        return SimpleNamespace(
            name='Treino A',
            client=client,
            personal=personal,
            goal='Força',
            notes='Manter postura.',
            exercises=SimpleNamespace(all=lambda: [exercise]),
        )

    def test_builds_workout_message(self):
        message = build_workout_message(self._workout())

        self.assertIn('🏋️ *EVOLUTTY | FICHA DE TREINO*', message)
        self.assertIn('*01 · Agachamento*', message)
        self.assertIn('4 séries × 12 repetições', message)
        self.assertIn('*📝 OBSERVAÇÕES*', message)
        self.assertIn('Manter postura.', message)

    @override_settings(
        EVOLUTION_API_URL='https://evolution.example.com/',
        EVOLUTION_API_KEY='secret',
        EVOLUTION_API_INSTANCE='personal',
    )
    @patch('personais.services.requests.post')
    def test_sends_workout_to_evolution(self, post):
        post.return_value = Mock()
        workout = self._workout()

        send_workout_message(workout)

        post.assert_called_once()
        self.assertEqual(
            post.call_args.args[0],
            'https://evolution.example.com/message/sendText/personal',
        )
        self.assertEqual(
            post.call_args.kwargs['json']['number'], '5511999998888')
        post.return_value.raise_for_status.assert_called_once_with()

    def test_rejects_invalid_phone(self):
        with self.assertRaises(EvolutionAPIError):
            with override_settings(
                    EVOLUTION_API_URL='https://evolution.example.com',
                    EVOLUTION_API_KEY='secret',
                    EVOLUTION_API_INSTANCE='personal',
            ):
                send_workout_message(self._workout(phone='123'))


class WorkoutExerciseFormSetTests(SimpleTestCase):
    def test_normalizes_exercise_order_per_workout(self):
        personal = PersonalTrainer(
            first_name='Carlos',
            email='carlos@example.com',
        )
        client = PersonalClient(
            personal=personal,
            first_name='Ana',
        )
        workout = Workout(
            personal=personal,
            client=client,
            name='Treino A',
        )
        data = {
            'exercises-TOTAL_FORMS': '2',
            'exercises-INITIAL_FORMS': '0',
            'exercises-MIN_NUM_FORMS': '0',
            'exercises-MAX_NUM_FORMS': '1000',
            'exercises-0-order': '99',
            'exercises-0-name': 'Agachamento',
            'exercises-0-sets': '3',
            'exercises-0-reps': '12',
            'exercises-0-load': '',
            'exercises-0-rest_seconds': '60',
            'exercises-0-DELETE': '',
            'exercises-1-order': '99',
            'exercises-1-name': 'Supino',
            'exercises-1-sets': '3',
            'exercises-1-reps': '10',
            'exercises-1-load': '',
            'exercises-1-rest_seconds': '60',
            'exercises-1-DELETE': '',
        }

        formset = WorkoutExerciseFormSet(data=data, instance=workout)

        self.assertTrue(formset.is_valid())
        self.assertEqual(
            [form.cleaned_data['order'] for form in formset.forms], [1, 2])
