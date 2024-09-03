from django.db import models

# Create your models here.
class Forecast(models.Model):
    date = models.DateField()
    forecasted = models.FloatField()
    product = models.CharField(max_length=100)
    category = models.CharField(max_length=100)

