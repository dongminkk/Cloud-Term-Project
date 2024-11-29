from django.urls import path
from . import views

urlpatterns = [
    path('operations/', views.ec2_operations, name='ec2_operations'),
]
