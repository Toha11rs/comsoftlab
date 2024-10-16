from django.urls import path
from MailApp import consumers

websocket_urlpatterns = [
    path('ws/letters/', consumers.MessageConsumer.as_asgi()),
]
