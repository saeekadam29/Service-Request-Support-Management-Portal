from django.urls import path

from . import views

app_name = 'tickets'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.ticket_list_view, name='ticket_list'),
    path('create/', views.ticket_create_view, name='ticket_create'),
    path('<int:pk>/', views.ticket_detail_view, name='ticket_detail'),
    path('<int:pk>/edit/', views.ticket_update_view, name='ticket_update'),
    path('<int:pk>/delete/', views.ticket_delete_view, name='ticket_delete'),
]
