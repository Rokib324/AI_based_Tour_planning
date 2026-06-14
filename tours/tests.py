# pyrefly: ignore [missing-import]
from django.test import TestCase
# pyrefly: ignore [missing-import]
from django.contrib.auth import get_user_model
# pyrefly: ignore [missing-import]
from tours.models import CustomTour, ItineraryItem
from decimal import Decimal

User = get_user_model()

class CustomTourTestCase(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='testclient',
            email='testclient@example.com',
            password='testpassword',
            role='client'
        )
        self.manager_user = User.objects.create_user(
            username='testmanager',
            email='testmanager@example.com',
            password='testpassword',
            role='tour_manager'
        )

    def test_tour_creation_and_pricing_calculation(self):
        tour = CustomTour.objects.create(
            client=self.client_user,
            title='Test Adventure',
            start_date='2026-07-01',
            end_date='2026-07-05',
            status='draft',
            service_fee=Decimal('50.00'),
            markup_amount=Decimal('0.00')
        )
        
        ItineraryItem.objects.create(
            custom_tour=tour,
            day_number=1,
            activity_title='Day 1 activity',
            estimated_cost=Decimal('120.00')
        )
        ItineraryItem.objects.create(
            custom_tour=tour,
            day_number=2,
            activity_title='Day 2 activity',
            estimated_cost=Decimal('80.00')
        )

        tour.recalculate_prices()
        tour.save()

        self.assertEqual(tour.base_cost, Decimal('200.00'))
        self.assertEqual(tour.total_price, Decimal('250.00'))

        tour.markup_amount = Decimal('100.00')
        tour.recalculate_prices()
        tour.save()
        
        self.assertEqual(tour.total_price, Decimal('350.00'))

