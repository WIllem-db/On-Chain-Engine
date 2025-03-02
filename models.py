from mongoengine import Document, StringField, FloatField, DateTimeField, IntField, ListField, ReferenceField, URLField
from datetime import datetime, timedelta


class Coin(Document):
    """Model for cryptocurrency information"""
    # Core identifiers
    id = StringField(primary_key=True)  # CoinGecko ID
    symbol = StringField(required=True, unique=True)
    name = StringField(required=True)

    # Market data
    market_cap_rank = IntField()
    current_price = FloatField()
    market_cap = FloatField()
    total_volume = FloatField()

    # Price changes
    price_change_percentage_1h = FloatField()
    price_change_percentage_24h = FloatField()
    price_change_percentage_7d = FloatField()
    price_change_percentage_30d = FloatField()

    # Additional metadata
    image = URLField()
    sector = StringField()
    categories = ListField(StringField())

    # Tracking
    last_updated = DateTimeField(default=datetime.utcnow)

    meta = {
        'indexes': [
            'symbol',
            'market_cap_rank'
        ],
        'ordering': ['market_cap_rank']
    }

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class PriceHistory(Document):
    """Model for historical price data points"""
    symbol = StringField(required=True)
    price = FloatField(required=True)
    timestamp = DateTimeField(required=True, default=datetime.utcnow)

    meta = {
        'indexes': [
            {'fields': ['symbol', 'timestamp'], 'unique': True},
            {'fields': ['timestamp']}
        ],
        'ordering': ['timestamp']
    }

    def __str__(self):
        return f"{self.symbol} - {self.price} @ {self.timestamp}"
