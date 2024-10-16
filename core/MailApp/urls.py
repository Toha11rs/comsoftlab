from django.urls import path

from MailApp import views

app_name = 'mail'

urlpatterns = [

    path('my_mails_create', views.MailFormView.as_view(), name='my_mails_create'),
    path('my_mails/<pk>', views.MailUpdateView.as_view(), name='my_mails_update'),

    path('download_mail',views.download_mail, name='download_mail'),
    path('all_mails', views.all_mails, name='all_mails'),
]
