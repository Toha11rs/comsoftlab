from django.db import models
from django.shortcuts import reverse


class MailType(models.Model):
    name = models.CharField(max_length=25)
    login = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    imap_server = models.CharField(max_length=52)

    def __str__(self):
        return f"{self.name} - {self.login}"

    def get_absolute_url(self):
        return reverse("mail:my_mails_update", args=[str(self.id)])


class Letter(models.Model):
    uid = models.IntegerField()
    theme = models.CharField(max_length=255, null=True)
    text = models.TextField(null=True)
    file = models.TextField(default="[]")
    dispatch_date = models.DateTimeField()
    receipt_date = models.DateTimeField(auto_now_add=True)
    type_mail = models.ForeignKey('MailApp.MailType', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.uid} - {self.theme}"
