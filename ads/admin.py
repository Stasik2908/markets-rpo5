from django.contrib import admin
from .models import Ad, Category, Favorite, Review
# Register your models here.

admin.site.register(Category)
admin.site.register(Ad)
admin.site.register(Review)
admin.site.register(Favorite)
