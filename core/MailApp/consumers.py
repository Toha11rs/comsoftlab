import asyncio
import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from MailApp.components.channels import download_mail_progress
from MailApp.models import MailType


class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        try:
            all_mails = await sync_to_async(list)(MailType.objects.all())
        except Exception as e:
            await self.close()
            return

        for mail in all_mails:
            asyncio.create_task(self.start_mail_download(mail))

    async def start_mail_download(self, mail):
        await download_mail_progress(mail.name, self)

    async def disconnect(self, close_code):
        await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def send_progress(self, progress, status):
        await self.send(text_data=json.dumps({
            'progress': progress,
            'status': status,
        }))

    async def send_new_message(self, letter):
        await self.send(text_data=json.dumps({
            'new_message': {
                'uid': letter.uid,
                'type_mail': letter.type_mail.name,
                'theme': letter.theme,
                'text': letter.text,
                'dispatch_date': str(letter.dispatch_date),
                'receipt_date': str(letter.receipt_date),
                'attachments': letter.file,
            }
        }))
