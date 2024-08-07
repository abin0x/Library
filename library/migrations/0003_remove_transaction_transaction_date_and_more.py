# Generated by Django 5.0.6 on 2024-07-13 08:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_alter_book_borrowing_price_alter_book_categories_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='transaction_date',
        ),
        migrations.AddField(
            model_name='transaction',
            name='borrow_date',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name='transaction',
            name='return_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
