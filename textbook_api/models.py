from django.db import models

# Create your models here.
from django.db import models

class Textbook(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='textbooks/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)