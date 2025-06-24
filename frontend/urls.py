from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_home, name='chatbot_home'),  # For loading the chatbot UI
    path('get_chatbot_response/', views.get_chatbot_response, name='get_chatbot_response'),  # For handling chatbot input
]
