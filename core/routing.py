from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/support/<int:user_id>/', consumers.SupportChatConsumer.as_asgi()),
    path('ws/home-stats/', consumers.HomeStatsConsumer.as_asgi()),
]
