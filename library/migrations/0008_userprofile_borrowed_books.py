# Generated by Django 5.0.6 on 2024-07-13 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0007_alter_review_book'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='borrowed_books',
            field=models.ManyToManyField(blank=True, related_name='borrowed_by', to='library.book'),
        ),
    ]
