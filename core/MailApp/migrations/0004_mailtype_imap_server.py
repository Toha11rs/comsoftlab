# Generated by Django 5.1.2 on 2024-10-14 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MailApp', '0003_alter_letter_theme'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailtype',
            name='imap_server',
            field=models.CharField(default=1, max_length=52),
            preserve_default=False,
        ),
    ]
