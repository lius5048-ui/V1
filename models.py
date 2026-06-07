from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    title = db.Column(db.Text, default="")
    brand = db.Column(db.String(200), default="")
    category = db.Column(db.String(100), default="")
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default="USD")
    rating = db.Column(db.Float, nullable=True)
    review_count = db.Column(db.Integer, default=0)
    availability = db.Column(db.String(100), default="")
    description = db.Column(db.Text, default="")
    specs = db.Column(db.Text, default="{}")  # JSON
    images = db.Column(db.Text, default="[]")  # JSON
    url = db.Column(db.Text, default="")
    crawl_time = db.Column(db.String(30), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)

    reviews = db.relationship("Review", backref="product", lazy="dynamic",
                              order_by="Review.rating")
    related = db.relationship("RelatedProduct", backref="product", lazy="dynamic")


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey("products.product_id"), index=True)
    rating = db.Column(db.Integer, default=0)
    title = db.Column(db.Text, default="")
    body = db.Column(db.Text, default="")
    date = db.Column(db.String(30), default="")
    helpful_count = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    user_nickname = db.Column(db.String(100), default="")
    created_at = db.Column(db.DateTime, default=datetime.now)


class RelatedProduct(db.Model):
    __tablename__ = "related_products"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey("products.product_id"), index=True)
    related_id = db.Column(db.String(50), default="")
    title = db.Column(db.Text, default="")
    price = db.Column(db.Float, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    review_count = db.Column(db.Integer, default=0)
    url = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now)


class ReviewAnalysis(db.Model):
    __tablename__ = "review_analysis"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), db.ForeignKey("products.product_id"), index=True)
    analysis_text = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.now)
