from asgiref.sync import sync_to_async
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView, UpdateView

from MailApp.components import functions
from MailApp.components.functions import save_mail
from MailApp.forms import MailForm
from MailApp.models import MailType, Letter


class MailFormView(FormView):
    template_name = "MailApp/my_mails_create.html"
    form_class = MailForm
    success_url = "/"

    def form_valid(self, form):
        MailType.objects.create(**form.cleaned_data)
        return super().form_valid(form)


class MailUpdateView(UpdateView):
    model = MailType
    fields = ["login", "password"]
    template_name_suffix = "_update_form"


def my_mails(request):
    context = {
        "my_mails": MailType.objects.all()
    }
    return render(request, "MailApp/my_mails.html",context)

def download_mail(request):
    mail_type = "mail.ru"
    imap = functions.connect_to_mailbox(mail_type)

    res, unseen_msg = imap.uid("search", None, "ALL")
    unseen_msg = unseen_msg[0].decode(encoding="utf-8").split()
    last_uid = sync_to_async(Letter.objects.all().order_by('-uid').first())
    new_uids = [uid for uid in unseen_msg if int(uid) > last_uid.uid]
    print(new_uids)
    if len(new_uids) > 0:
        save_mail(new_uids, imap, mail_type)
        return HttpResponse(200)
    else:
        return HttpResponse("No emails found", status=404)


def all_mails(request):
    return render(request, 'MailApp/AllMail.html')
