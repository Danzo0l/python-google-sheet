from django.db import models
from django.utils import timezone
# Create your models here.


class Row(models.Model):
    number = models.IntegerField(verbose_name='Номер заказа', default=0, unique=True)
    priceUSD = models.FloatField(verbose_name='Стоимость, $', default=0)
    priceRUB = models.FloatField(verbose_name='Стоимость, ₽', default=0)
    supply = models.DateTimeField(verbose_name='Срок поставки', null=True)

    def __str__(self):
        return str(self.number)
