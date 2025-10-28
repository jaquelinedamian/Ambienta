from django.core.management.base import BaseCommand
from ml_models.models import MLModel

class Command(BaseCommand):
    help = 'Verifica o status dos modelos ML'

    def handle(self, *args, **options):
        self.stdout.write('Verificando status dos modelos ML...\n')
        
        try:
            models = MLModel.objects.filter(is_active=True)
            
            if models.exists():
                self.stdout.write(self.style.SUCCESS(f'Encontrados {models.count()} modelos ativos:'))
                for model in models:
                    self.stdout.write(f'- {model.model_type} (criado em: {model.created_at})')
            else:
                self.stdout.write(self.style.WARNING('Nenhum modelo ML ativo encontrado'))
                self.stdout.write('Use python manage.py train_ml_models para treinar os modelos')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao verificar status: {str(e)}')
            )