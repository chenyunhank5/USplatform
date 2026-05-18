import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

from .models import SupportMessage


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
                'message': saved_message['message'],
                'sender_id': saved_message['sender_id'],
                'sender_username': saved_message['sender_username'],
                'sender_is_staff': saved_message['sender_is_staff'],
                'created_at': saved_message['created_at'],
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'sender_is_staff': event['sender_is_staff'],
            'created_at': event['created_at'],
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

        return {
            'message': obj.message,
            'sender_id': sender.id,
            'sender_username': sender.username,
            'sender_is_staff': sender.is_staff,
            'created_at': obj.created_at.strftime('%H:%M'),
        }
