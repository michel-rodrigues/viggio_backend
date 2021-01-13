from django.db import models

from orders.models import Order
from utils.base_models import BaseModel


class WirecardTransactionData(BaseModel):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='third_party_transaction',
    )
    wirecard_order_hash = models.CharField(max_length=50)
    wirecard_payment_hash = models.CharField(max_length=50)
    payment_event_last_timestamp = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.order.hash_id)
