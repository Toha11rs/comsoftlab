# Generated by Django 5.1.2 on 2024-10-14 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MailApp', '0002_alter_letter_file_alter_letter_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='letter',
            name='theme',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
