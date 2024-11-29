from django.urls import path
from . import views

urlpatterns = [
    path('instances/', views.list_instances, name='list_instances'),  # 인스턴스 목록
]
