from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DestinationViewSet, TourPackageViewSet, CustomTourViewSet

router = DefaultRouter()
router.register('destinations', DestinationViewSet, basename='destination')
router.register('packages', TourPackageViewSet, basename='tourpackage')
router.register('custom-tours', CustomTourViewSet, basename='customtour')

urlpatterns = [
    path('', include(router.urls)),
]
