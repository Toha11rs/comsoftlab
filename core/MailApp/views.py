from django.shortcuts import render
from django.views.generic.edit import FormView, UpdateView

from MailApp.forms import MailForm
from MailApp.models import MailType


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


def all_mails(request):
    return render(request, 'MailApp/AllMail.html')
