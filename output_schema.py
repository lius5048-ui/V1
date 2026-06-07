from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Review(BaseModel):
    rating: float
    title: Optional[str] = ""
    body: str
    date: Optional[str] = ""
    helpful_count: Optional[int] = 0
    verified_purchase: Optional[bool] = False


class ProductBasic(BaseModel):
    product_id: str
    title: str
    price: Optional[float] = None
    currency: str = "USD"
    brand: Optional[str] = ""
    sku: Optional[str] = ""
    rating: Optional[float] = None
    review_count: Optional[int] = 0
    availability: Optional[str] = ""
    url: str


class ProductDetails(BaseModel):
    description: Optional[str] = ""
    specs: dict = {}
    images: list[str] = []


class ReviewSummary(BaseModel):
    total_reviews: int
    main_product_rating: Optional[float] = None
    negative_reviews: list[Review] = []
    negative_topics: dict = {}
    positive_summary: Optional[str] = ""
    negative_summary: Optional[str] = ""


class CrawlOutput(BaseModel):
    query: str
    main_product: Optional[ProductBasic] = None
    details: Optional[ProductDetails] = None
    review_analysis: Optional[ReviewSummary] = None
    related_products: list[ProductBasic] = []
    crawl_time: str = ""
    errors: list[str] = []
