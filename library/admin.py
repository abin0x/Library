# admin.py

from django.contrib import admin
from .models import Book, Category,Transaction

admin.site.register(Book)
admin.site.register(Category)
admin.site.register(Transaction)
