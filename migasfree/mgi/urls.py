from django.urls import path
from rest_framework import routers

from migasfree.mgi.views import BuildViewSet, ConfigViewSet, FlavourViewSet, ReleaseViewSet

router = routers.DefaultRouter()
router.register(r'config', ConfigViewSet)
router.register(r'flavour', FlavourViewSet)
router.register(r'release', ReleaseViewSet)
router.register(r'build', BuildViewSet)

urlpatterns = [
    *router.urls,
]
