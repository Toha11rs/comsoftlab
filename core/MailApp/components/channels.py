import asyncio
import logging

from asgiref.sync import sync_to_async

from MailApp.models import Letter
from . import functions
from .functions import save_mail

logger = logging.getLogger(__name__)


async def download_mail_progress(mail_type, consumer, interval=10):
    """
    Асинхронная функция для периодической проверки новых писем.

    :param mail_type: Тип почты, к которому подключаемся.
    :param consumer: Веб-сокетный потребитель для отправки прогресса и новых писем.
    :param interval: Интервал в секундах между проверками новых писем.
    """
    logger.info("Подключаемся к почтовому ящику для %s", mail_type)
    imap = await functions.connect_to_mailbox(mail_type)

    while True:
        logger.debug("Проверка новых писем...")
        res, all_msg = imap.uid("search", None, "ALL")
        all_msg = all_msg[0].decode(encoding="utf-8").split()

        last_uid = await sync_to_async(Letter.objects.order_by('-uid').first)()
        if last_uid is not None:
            new_uids = [uid for uid in all_msg if int(uid) > int(last_uid.uid)]
        else:
            new_uids = [uid for uid in all_msg]

        logger.info("Найдено новых писем: %d", len(new_uids))

        if new_uids:
            await save_and_process_new_mail(new_uids, imap, mail_type, consumer)

        await asyncio.sleep(interval)


async def save_and_process_new_mail(new_uids, imap, mail_type, consumer):
    """
    Функция для обработки и сохранения новых писем.

    :param new_uids: Список UID новых писем.
    :param imap: Подключение к почтовому ящику.
    :param mail_type: Тип почты.
    :param consumer: Веб-сокетный потребитель для отправки новых сообщений.
    """
    total = len(new_uids)
    checked = 0

    for uid in new_uids:
        checked += 1
        progress = int((checked / total) * 100)

        await consumer.send_progress(progress, "Получение сообщений...")

        logger.debug("Обработка письма с UID: %s (прогресс: %d%%)", uid, progress)

        try:
            msg, letter = await save_mail(new_uids=[uid],
                                          imap=imap,
                                          mail_type=mail_type)
            await consumer.send_new_message(letter)
            logger.info("Письмо с UID %s успешно сохранено.", uid)
        except Exception as e:
            logger.error("Ошибка при обработке письма с UID %s: %s", uid, str(e))

    await consumer.send_progress(100, "Загрузка новых писем завершена")
    logger.info("Загрузка почты завершена.")
