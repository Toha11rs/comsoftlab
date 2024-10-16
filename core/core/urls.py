from django.contrib import admin
from django.urls import path, include

from MailApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.my_mails, name='my_mails'),
    path('mail/', include('MailApp.urls')),
]
