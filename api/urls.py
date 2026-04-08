from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'insights', views.InsightViewSet, basename='insight')
router.register(r'recommendations', views.RecommendationViewSet, basename='recommendation')

urlpatterns = [
    path('', include(router.urls)),
]