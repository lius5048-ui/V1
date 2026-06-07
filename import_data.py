#!/usr/bin/env python3
"""Import cached JSON data into SQLite database."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import db, app
from models import Product, Review, RelatedProduct, ReviewAnalysis

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def import_json(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    pid = data["details"].get("product_id") or data["main_product"].get("product_id", "")
    exists = Product.query.filter_by(product_id=pid).first()
    if exists:
        print(f"  Skipping {pid} — already in DB")
        return

    d = data["details"]
    mp = data["main_product"]

    product = Product(
        product_id=pid,
        title=d.get("title", mp.get("title", "")),
        brand=d.get("brand", mp.get("brand", "")),
        category=d.get("category", ""),
        price=d.get("price", mp.get("price")),
        currency=d.get("currency", "USD"),
        rating=d.get("rating", mp.get("rating")),
        review_count=d.get("review_count", mp.get("review_count", 0)),
        availability=str(d.get("availability", "")),
        description=d.get("description", ""),
        specs=json.dumps(d.get("specs", {}), ensure_ascii=False),
        images=json.dumps(d.get("images", []), ensure_ascii=False),
        url=d.get("url", mp.get("url", "")),
        crawl_time=data.get("crawl_time", ""),
    )
    db.session.add(product)

    for r in data["reviews"].get("all_reviews", []):
        review = Review(
            product_id=pid,
            rating=r.get("rating", 0),
            title=r.get("reviewTitle", r.get("title", "")),
            body=r.get("reviewText", r.get("body", r.get("text", ""))),
            date=r.get("reviewSubmissionTime", r.get("date", "")),
            helpful_count=r.get("helpful_count", r.get("positiveFeedback", 0)),
            verified=r.get("verified_purchase", r.get("verified", False)),
            user_nickname=r.get("userNickname", r.get("user_nickname", "")),
        )
        db.session.add(review)

    for rp in data.get("related_products", []):
        r = RelatedProduct(
            product_id=pid,
            related_id=rp.get("product_id", ""),
            title=rp.get("title", ""),
            price=rp.get("price"),
            rating=rp.get("rating"),
            review_count=rp.get("review_count", 0),
            url=rp.get("url", ""),
        )
        db.session.add(r)

    db.session.commit()
    neg = len(data["reviews"].get("negative_reviews", []))
    total = data["reviews"].get("total_reviews", 0)
    print(f"  ✓ {pid}: {d.get('title',mp.get('title',''))[:50]}... ({total} reviews, {neg} negative)")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "crawl_*.json")))
        if not files:
            print("No crawl JSON files found in output/")
            print("Run main.py first to crawl products.")
            sys.exit(1)

        for fp in files:
            print(f"Importing {os.path.basename(fp)}...")
            import_json(fp)

        print(f"\nDone! {Product.query.count()} product(s) in database.")
