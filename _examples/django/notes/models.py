from django.db import models


class Note(models.Model):
    text = models.CharField(max_length=200)
