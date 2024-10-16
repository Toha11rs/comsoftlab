from django import forms

from MailApp.models import MailType


class MailForm(forms.ModelForm):
    class Meta:
        model = MailType
        fields = ['name', 'login', 'password', "imap_server"]
