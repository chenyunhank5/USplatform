import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from .home_stats import build_chart_paths
from .models import SupportMessage
from .models import HomePageSettings


class SupportChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.chat_user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f"support_chat_{self.chat_user_id}"

        user = self.scope["user"]

        if user.is_anonymous:
            await self.close()
            return

        if not user.is_staff and user.id != self.chat_user_id:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        sender = self.scope["user"]

        if not message:
            return

        saved_message = await self.save_message(sender, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'id': saved_message['id'],
                'message': saved_message['message'],
                'sender_id': saved_message['sender_id'],
                'sender_username': saved_message['sender_username'],
                'sender_is_staff': saved_message['sender_is_staff'],
                'created_at': saved_message['created_at'],
                'created_date': saved_message['created_date'],
                'created_date_display': saved_message['created_date_display'],
                'image_url': '',
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_is_staff': event['sender_is_staff'],
            'created_at': event['created_at'],
            'created_date': event['created_date'],
            'created_date_display': event['created_date_display'],
            'image_url': event.get('image_url', ''),
            'id': event.get('id'),
        }))

    @database_sync_to_async
    def save_message(self, sender, message):
        chat_user = User.objects.get(id=self.chat_user_id)

        obj = SupportMessage.objects.create(
            user=chat_user,
            sender=sender,
            message=message,
            message_type='text',
            is_read_by_user=True if not sender.is_staff else False,
            is_read_by_staff=True if sender.is_staff else False,
        )

        local_created_at = timezone.localtime(obj.created_at)

        return {
            'id': obj.id,
            'message': obj.message,
            'sender_id': sender.id,
            'sender_username': sender.username,
            'sender_is_staff': sender.is_staff,
            'created_at': local_created_at.strftime('%H:%M'),
            'created_date': local_created_at.strftime('%Y-%m-%d'),
            'created_date_display': local_created_at.strftime('%B %d, %Y'),
        }


class HomeStatsConsumer(AsyncWebsocketConsumer):
    group_name = 'homepage_stats'

    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_stats()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def homepage_stats(self, event):
        await self.send_stats(event.get('stats'))

    async def send_stats(self, stats=None):
        if stats is None:
            stats = await self.get_stats()
        await self.send(text_data=json.dumps(stats))

    @database_sync_to_async
    def get_stats(self):
        settings = HomePageSettings.objects.first()
        values = {
            'online_users_value': self.parse_value(settings.online_users_value),
            'order_completion_value': self.parse_value(settings.order_completion_value),
            'optimize_demand_value': self.parse_value(settings.optimize_demand_value),
            'order_quantity_value': self.parse_value(settings.order_quantity_value),
        }
        return {
            'online_users_value': settings.online_users_value,
            'order_completion_value': settings.order_completion_value,
            'optimize_demand_value': settings.optimize_demand_value,
            'order_quantity_value': settings.order_quantity_value,
            'charts': build_chart_paths(values),
        }

    @staticmethod
    def parse_value(value):
        text = str(value or '').lower()
        multiplier = 1000 if 'k' in text else 1
        number = ''.join(character for character in text if character.isdigit() or character == '.')
        try:
            return round(float(number) * multiplier)
        except ValueError:
            return 0
