from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TicketViewSet, CategoryViewSet, CommentViewSet

router = DefaultRouter()
router.register('tickets', TicketViewSet, basename='ticket')
router.register('categories', CategoryViewSet, basename='category')
router.register('comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]
