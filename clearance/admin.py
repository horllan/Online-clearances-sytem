from django.contrib import admin
# Register your models here.
from . import models
admin.site.register(models.Student)
admin.site.register(models.Staff)
admin.site.register(models.ClearanceForm)
admin.site.register(models.ClearanceSection)
admin.site.register(models.Notification)