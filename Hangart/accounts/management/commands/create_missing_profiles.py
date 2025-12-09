from django.core.management.base import BaseCommand
from accounts.models import User, ArtistProfile, BuyerProfile, AdminProfile


class Command(BaseCommand):
    help = 'Create missing profiles for existing users'

    def handle(self, *args, **options):
        self.stdout.write('Creating missing profiles...')
        
        created_artist = 0
        created_buyer = 0
        created_admin = 0
        
        # Get all users
        users = User.objects.all()
        
        for user in users:
            if user.role == 'artist':
                profile, created = ArtistProfile.objects.get_or_create(user=user)
                if created:
                    created_artist += 1
                    self.stdout.write(f'Created ArtistProfile for {user.username}')
            
            elif user.role == 'buyer':
                profile, created = BuyerProfile.objects.get_or_create(user=user)
                if created:
                    created_buyer += 1
                    self.stdout.write(f'Created BuyerProfile for {user.username}')
            
            elif user.role == 'admin':
                profile, created = AdminProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'employee_id': f'EMP{user.id:04d}',
                        'position': 'Admin'
                    }
                )
                if created:
                    created_admin += 1
                    self.stdout.write(f'Created AdminProfile for {user.username}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCompleted! Created:\n'
            f'  - {created_artist} ArtistProfile(s)\n'
            f'  - {created_buyer} BuyerProfile(s)\n'
            f'  - {created_admin} AdminProfile(s)'
        ))
