from django.contrib import admin
from score import models

admin.site.register(models.Question)
admin.site.register(models.Presentation)
admin.site.register(models.Point)
