from django.urls import re_path
# from . import consumers
from chat.consumers import TestConsumer

websockets_urlpatterns = [
    re_path(r'ws/socket-server/', TestConsumer.as_asgi()),
]