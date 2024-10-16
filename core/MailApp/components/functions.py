import base64
import email
import imaplib
import logging
import os
import quopri
from datetime import datetime
from email.header import decode_header

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup

from MailApp.models import MailType, Letter

logger = logging.getLogger(__name__)


def decode_mime_words(s):
    decoded_string = ''
    for word, encoding in decode_header(s):
        if isinstance(word, bytes):
            if encoding:
                decoded_string += word.decode(encoding)
            else:
                decoded_string += word.decode('utf-8', errors='replace')
        else:
            decoded_string += word
    return decoded_string


def save_file_to_attachment(filepath, part):
    with open(filepath, 'wb') as f:
        f.write(part.get_payload(decode=True))


async def save_file_to_letter(letter_instance, filename_list):
    letter_instance.file = filename_list
    await sync_to_async(letter_instance.save)()


async def download_attachments_in_email(msg, letter_instance):
    outputdir = f'attachments/{letter_instance.id}'
    filename_list = []

    for part in msg.walk():
        filename = part.get_filename()
        if filename:
            if not await sync_to_async(os.path.exists)(outputdir):
                await sync_to_async(os.makedirs)(outputdir)
            filename = decode_mime_words(filename)
            filename_list.append(filename)

            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                filepath = os.path.join(outputdir, filename)

                await sync_to_async(save_file_to_attachment)(filepath, part)

    await save_file_to_letter(letter_instance, filename_list)


async def connect_to_mailbox(mailbox_name):
    mail_ru = await sync_to_async(MailType.objects.get)(name=mailbox_name)
    print("mail", mail_ru)
    mail_pass = mail_ru.password
    username = mail_ru.login
    imap_server = mail_ru.imap_server

    try:
        imap = imaplib.IMAP4_SSL(imap_server)
        imap.login(username, mail_pass)
        imap.select("INBOX")
        return imap

    except imaplib.IMAP4.abort as e:
        print(f"IMAP connection aborted: {e}")
        await connect_to_mailbox(mailbox_name)


async def date_parse(msg_date):
    if not msg_date:
        return datetime.now()
    else:
        dt_obj = "".join(str(msg_date[:6]))
        dt_obj = dt_obj.strip("'(),")
        dt_obj = datetime.strptime(dt_obj, "%Y, %m, %d, %H, %M, %S")
        return dt_obj


async def from_subj_decode(msg_from_subj):
    if msg_from_subj:
        encoding = decode_header(msg_from_subj)[0][1]
        msg_from_subj = decode_header(msg_from_subj)[0][0]
        if isinstance(msg_from_subj, bytes):
            msg_from_subj = msg_from_subj.decode(encoding)
        if isinstance(msg_from_subj, str):
            pass
        msg_from_subj = str(msg_from_subj).strip("<>").replace("<", "")
        return msg_from_subj
    else:
        return None


def get_letter_text_from_html(body):
    body = body.replace("<div><div>", "<div>").replace("</div></div>", "</div>")
    try:
        soup = BeautifulSoup(body, "html.parser")
        paragraphs = soup.find_all("div")
        text = ""
        for paragraph in paragraphs:
            text += paragraph.text + "\n"
        return text.replace("\xa0", " ")
    except (Exception) as exp:
        print("text ftom html err ", exp)
        return False


def letter_type(part):
    if part["Content-Transfer-Encoding"] in (None, "7bit", "8bit", "binary"):
        return part.get_payload()
    elif part["Content-Transfer-Encoding"] == "base64":
        encoding = part.get_content_charset()
        return base64.b64decode(part.get_payload()).decode(encoding)
    elif part["Content-Transfer-Encoding"] == "quoted-printable":
        encoding = part.get_content_charset()
        return quopri.decodestring(part.get_payload()).decode(encoding)
    else:
        return part.get_payload()


async def get_letter_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            count = 0
            if part.get_content_maintype() == "text" and count == 0:
                extract_part = letter_type(part)
                if part.get_content_subtype() == "html":
                    letter_text = get_letter_text_from_html(extract_part)
                else:
                    letter_text = extract_part.rstrip().lstrip()
                count += 1
                return (
                    letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")
                )
    else:
        count = 0
        if msg.get_content_maintype() == "text" and count == 0:
            extract_part = letter_type(msg)
            if msg.get_content_subtype() == "html":
                letter_text = get_letter_text_from_html(extract_part)
            else:
                letter_text = extract_part
            count += 1
            return letter_text.replace("<", "").replace(">", "").replace("\xa0", " ")


async def save_mail(new_uids: list, imap, mail_type: str):
    for uid in new_uids:
        res, msg = imap.uid("fetch", uid, "(RFC822)")
        if res == "OK":
            msg = email.message_from_bytes(msg[0][1])

            msg_date = await date_parse(email.utils.parsedate_tz(msg["Date"]))
            msg_subj = await from_subj_decode(msg["Subject"])
            msg_letter = await get_letter_text(msg)
            mail_type_instance = await sync_to_async(MailType.objects.get)(name=mail_type)

            logger.info(f"Обработка письма c uid: {uid}")
            letter_instance = await sync_to_async(Letter.objects.filter(uid=uid, type_mail=mail_type_instance).first)()
            if letter_instance is None:
                letter_instance = await sync_to_async(Letter.objects.create)(
                    uid=uid,
                    theme=msg_subj,
                    text=msg_letter,
                    dispatch_date=msg_date,
                    type_mail=mail_type_instance
                )
                logger.info(f"Создан новый Letter c UID: {uid}")

            if msg.is_multipart():
                await download_attachments_in_email(msg, letter_instance)

            return msg, letter_instance
        else:
            logger.error(f"Ошибка обработки письма: {uid}. Response: {res}")
