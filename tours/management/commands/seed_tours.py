from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tours.models import Destination, TourPackage, ItineraryItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds destinations, packages and itinerary items'

    def handle(self, *args, **options):
        # 1. Create Destinations
        destinations = [
            {'name': 'Paris', 'country': 'France', 'description': 'The city of love and lights.', 'average_daily_cost': 150.00},
            {'name': 'Bali', 'country': 'Indonesia', 'description': 'Tropical paradise with beaches and culture.', 'average_daily_cost': 50.00},
            {'name': 'Tokyo', 'country': 'Japan', 'description': 'Ultramodern meet traditional temples.', 'average_daily_cost': 120.00},
            {'name': 'Rome', 'country': 'Italy', 'description': 'A historic city of art, food and architecture.', 'average_daily_cost': 130.00},
        ]

        for dest_data in destinations:
            dest, created = Destination.objects.get_or_create(
                name=dest_data['name'],
                country=dest_data['country'],
                defaults={'description': dest_data['description'], 'average_daily_cost': dest_data['average_daily_cost']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created destination: {dest.name}"))

        # 2. Get manager user
        manager = User.objects.filter(role='tour_manager').first()
        if not manager:
            manager = User.objects.filter(is_superuser=True).first()

        # 3. Create Packages
        packages_data = [
            {
                'title': 'Romantic Paris Getaway',
                'description': 'Enjoy a romantic weekend trip in Paris, visiting the Eiffel Tower, Seine River, and Louvre.',
                'duration_days': 5,
                'price': 999.00,
                'itinerary': [
                    {'day_number': 1, 'activity_title': 'Eiffel Tower & Seine Cruise', 'activity_description': 'Ascend the Eiffel Tower and enjoy a sunset cruise on the River Seine.', 'estimated_cost': 100.00},
                    {'day_number': 2, 'activity_title': 'Louvre Museum Tour', 'activity_description': 'Take a guided art tour inside the world-famous Louvre Museum.', 'estimated_cost': 80.00},
                    {'day_number': 3, 'activity_title': 'Palace of Versailles Excursion', 'activity_description': 'Explore the gold-gilded halls and grand gardens of Versailles.', 'estimated_cost': 120.00},
                    {'day_number': 4, 'activity_title': 'Montmartre Walk & French Dinner', 'activity_description': 'Walk around Sacré-Cœur and dine at a historic Parisian bistro.', 'estimated_cost': 150.00},
                    {'day_number': 5, 'activity_title': 'Champs-Élysées Shopping', 'activity_description': 'Window shop at luxury stores and enjoy café culture before departure.', 'estimated_cost': 50.00},
                ]
            },
            {
                'title': 'Bali Cultural Adventure',
                'description': 'Immerse yourself in Balinese temples, volcanic treks, and beautiful beaches.',
                'duration_days': 4,
                'price': 499.00,
                'itinerary': [
                    {'day_number': 1, 'activity_title': 'Arrival & Ubud Monkey Forest', 'activity_description': 'Check into Ubud resort and walk through the sacred monkey forest sanctuary.', 'estimated_cost': 30.00},
                    {'day_number': 2, 'activity_title': 'Mount Batur Sunrise Trek', 'activity_description': 'Hike up Mount Batur volcano at dawn for an unforgettable sunrise view.', 'estimated_cost': 70.00},
                    {'day_number': 3, 'activity_title': 'Uluwatu Temple & Dance Show', 'activity_description': 'Visit the cliffside temple and watch a traditional Kecak fire dance.', 'estimated_cost': 50.00},
                    {'day_number': 4, 'activity_title': 'Seminyak Surfing & Relaxation', 'activity_description': 'Relax by the ocean, take a quick surfing lesson, and depart.', 'estimated_cost': 40.00},
                ]
            }
        ]

        for pkg_info in packages_data:
            pkg, created = TourPackage.objects.get_or_create(
                title=pkg_info['title'],
                defaults={
                    'description': pkg_info['description'],
                    'duration_days': pkg_info['duration_days'],
                    'price': pkg_info['price'],
                    'created_by': manager
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created package: {pkg.title}"))
                for day_data in pkg_info['itinerary']:
                    ItineraryItem.objects.create(
                        tour_package=pkg,
                        day_number=day_data['day_number'],
                        activity_title=day_data['activity_title'],
                        activity_description=day_data['activity_description'],
                        estimated_cost=day_data['estimated_cost']
                    )
            else:
                self.stdout.write(self.style.WARNING(f"Package {pkg.title} already exists"))
