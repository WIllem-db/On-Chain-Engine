from mongoengine import Document, StringField, FloatField, DateTimeField, ListField, DictField
from datetime import datetime


# MongoDB model for cryptocurrency price history
class PriceHistory(Document):
    symbol = StringField(required=True)
    name = StringField(required=True)
    history = ListField(DictField())
    last_updated = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            'symbol',
            {'fields': ['last_updated']}
        ]
    }