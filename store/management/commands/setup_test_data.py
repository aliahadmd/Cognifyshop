from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Sets up initial test data for the store'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading initial data...')
        
        # Load fixtures
        call_command('loaddata', 'categories')
        call_command('loaddata', 'products')
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded initial data')) 