from enum import Enum

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class ReviewType(str, Enum):
    COMPLAINT = "complaint"
    GRATITUDE = "gratitude"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    REPEATED_CLAIM = "repeated_claim"


class Topic(str, Enum):
    DELIVERY = "delivery"
    PRODUCT_QUALITY = "product_quality"
    SUPPORT = "support"
    PRICE = "price"
    WEBSITE = "website"
    RETURN = "return"
    ASSORTMENT = "assortment"
    COMMUNICATION = "communication"
    OTHER = "other"


class ReviewAnalysis(BaseModel):
    sentiment: Sentiment
    review_type: ReviewType
    topic: Topic
    short_summary: str = Field(min_length=1, max_length=500)
    escalation_required: bool
    suggested_reply: str = Field(min_length=1, max_length=2000)
