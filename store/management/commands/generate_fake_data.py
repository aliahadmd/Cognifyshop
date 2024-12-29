from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product, Review
from faker import Faker
from django.utils.text import slugify
import random
from django.core.files.base import ContentFile
import requests
from io import BytesIO
from django.db import IntegrityError

fake = Faker()

class Command(BaseCommand):
    help = 'Generates fake data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generating fake data...')

        # Create superuser if it doesn't exist
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write('Created superuser: admin/admin')

        # Create test users
        users = []
        for _ in range(5):
            username = fake.user_name()
            while User.objects.filter(username=username).exists():
                username = fake.user_name()
            
            user = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='testpass123'
            )
            user.first_name = fake.first_name()
            user.last_name = fake.last_name()
            user.save()
            
            # Update profile
            user.profile.phone = fake.phone_number()
            user.profile.address = fake.street_address()
            user.profile.postal_code = fake.postcode()
            user.profile.city = fake.city()
            user.profile.save()
            
            users.append(user)
            self.stdout.write(f'Created user: {username}')

        # Create categories
        categories = [
            'Electronics',
            'Books',
            'Clothing',
            'Home & Kitchen',
            'Sports & Outdoors',
            'Toys & Games',
        ]

        for cat_name in categories:
            category, created = Category.objects.get_or_create(
                name=cat_name,
                slug=slugify(cat_name)
            )
            if created:
                self.stdout.write(f'Created category: {cat_name}')

        # Create products
        for category in Category.objects.all():
            for _ in range(random.randint(5, 10)):
                name = fake.catch_phrase()
                product = Product.objects.create(
                    category=category,
                    name=name,
                    slug=slugify(name),
                    description=fake.paragraph(nb_sentences=5),
                    price=round(random.uniform(9.99, 999.99), 2),
                    available=True
                )

                # Add a placeholder image from Lorem Picsum
                try:
                    width = random.randint(400, 800)
                    height = random.randint(400, 800)
                    image_url = f'https://picsum.photos/{width}/{height}'
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        image_name = f'product_{product.id}.jpg'
                        product.image.save(
                            image_name,
                            ContentFile(response.content),
                            save=True
                        )
                except Exception as e:
                    self.stdout.write(f'Failed to download image for {product.name}: {e}')

                self.stdout.write(f'Created product: {product.name}')

                # Add reviews from random users (without duplicates)
                review_users = random.sample(users, min(len(users), random.randint(0, 5)))
                for user in review_users:
                    try:
                        Review.objects.create(
                            product=product,
                            user=user,
                            rating=random.randint(1, 5),
                            comment=fake.paragraph(nb_sentences=3)
                        )
                        self.stdout.write(f'Added review by {user.username} for {product.name}')
                    except IntegrityError:
                        self.stdout.write(f'Skipped duplicate review by {user.username} for {product.name}')

        self.stdout.write(self.style.SUCCESS('Successfully generated fake data')) 