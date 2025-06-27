
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientFHIRViewSet

router = DefaultRouter()
router.register(r'patients', PatientFHIRViewSet)

urlpatterns = [
    path('', include(router.urls)),
]