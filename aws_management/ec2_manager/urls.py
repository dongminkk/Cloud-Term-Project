from django.urls import path
from . import views

urlpatterns = [
    path('operations/', views.ec2_operations, name='ec2_operations'),
    path('available-zones/', views.available_zones, name='available_zones'),
    path('available-regions/', views.available_regions, name='available_regions'),
    path('create-instance/', views.create_and_list_images, name='create_and_list_images'),
]
