import os, json, sys
from flask import Flask, render_template, request, jsonify
from models import db, Product, Review, RelatedProduct, ReviewAnalysis
from tools.walmart_crawler import search_products
from config import deepseek_client

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'walmart.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Error handlers — never expose source code
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="页面不存在"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="服务器内部错误"), 500

@app.errorhandler(Exception)
def all_exceptions(e):
    return render_template("error.html", code=500, message="服务器内部错误"), 500

db.init_app(app)

with app.app_context():
    db.create_all()


def _crawl_and_import(query: str) -> dict:
    """Crawl product, save JSON, import to DB. Returns dict with result."""
    sys.path.insert(0, basedir)

    # For numeric IDs crawl directly, for keywords search first
    if query.isdigit():
        from tools.walmart_crawler import fetch_product_details, fetch_product_reviews
        from tools.fetch_all_reviews import fetch_all_reviews
        from models import Product, Review, RelatedProduct, ReviewAnalysis

        details = fetch_product_details(query)
        all_reviews = fetch_all_reviews(query, max_pages=20)
        data = {
            "query": query,
            "crawl_time": __import__("datetime").datetime.now().isoformat(),
            "main_product": {"product_id": query, "title": details.get("title", ""),
                             "price": details.get("price"), "brand": details.get("brand", "")},
            "details": details,
            "reviews": all_reviews,
            "related_products": [],
        }
    else:
        from main import crawl as crawl_func
        data = crawl_func(query)

    pid = data["details"].get("product_id") or data["main_product"].get("product_id", "")

    import json as _json
    safe = __import__("re").sub(r'[\\/*?:"<>|]', "_", query)[:30]
    path = os.path.join(basedir, "output", f"crawl_{safe}.json")
    with open(path, "w", encoding="utf-8") as f:
        _json.dump(data, f, ensure_ascii=False, default=str, indent=2)

    with app.app_context():
        from import_data import import_json
        import_json(path)

    return {"success": True, "product_id": pid}


@app.route("/")
def index():
    products = Product.query.order_by(Product.created_at.desc()).all()
    total_reviews = sum(p.review_count or 0 for p in products)
    avg_rating = round(sum(p.rating or 0 for p in products) / len(products), 1) if products else 0
    brands = sorted(set(p.brand for p in products if p.brand))
    return render_template("index.html", products=products,
                           total_reviews=total_reviews, avg_rating=avg_rating,
                           brands=brands)


@app.route("/api/crawl", methods=["POST"])
def api_crawl():
    body = request.get_json()
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "error": "请输入商品ID或关键词"})

    # Check if already exists (if query is a product ID)
    existing = Product.query.filter_by(product_id=query).first()
    if existing:
        return jsonify({"success": True, "product_id": query,
                        "redirect": f"/product/{query}"})

    try:
        result = _crawl_and_import(query)
        return jsonify({"success": True, "product_id": result["product_id"],
                        "redirect": f"/product/{result['product_id']}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/search", methods=["POST"])
def api_search():
    """Search Walmart and return product list with DB status."""
    body = request.get_json()
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"products": []})

    try:
        results = search_products(query, limit=20)
        existing_ids = set(p.product_id for p in Product.query.all())
        products = []
        for r in results:
            pid = r.get("product_id", "")
            avail = r.get("availability", "")
            if isinstance(avail, dict):
                avail = avail.get("display", avail.get("value", ""))
            products.append({
                "product_id": pid,
                "title": r.get("title", ""),
                "brand": r.get("brand", ""),
                "price": r.get("price"),
                "rating": r.get("rating") if isinstance(r.get("rating"), (int, float)) else None,
                "review_count": r.get("review_count", 0),
                "availability": avail,
                "exists": pid in existing_ids,
            })
        return jsonify({"products": products})
    except Exception as e:
        return jsonify({"error": str(e), "products": []})


@app.route("/api/import-batch", methods=["POST"])
def api_import_batch():
    """Import selected product IDs from batch crawl."""
    body = request.get_json()
    ids = body.get("product_ids", [])
    if not ids:
        return jsonify({"imported": 0, "skipped": 0, "errors": 0})

    imported = 0
    skipped = 0
    errors = 0

    for pid in ids:
        existing = Product.query.filter_by(product_id=pid).first()
        if existing:
            skipped += 1
            continue
        try:
            result = _crawl_and_import(pid)
            if result["success"]:
                imported += 1
        except Exception:
            errors += 1

    return jsonify({"imported": imported, "skipped": skipped, "errors": errors})


@app.route("/product/<pid>")
def product_detail(pid):
    product = Product.query.filter_by(product_id=pid).first_or_404()
    reviews = Review.query.filter_by(product_id=pid).order_by(Review.rating).all()
    related = RelatedProduct.query.filter_by(product_id=pid).all()
    analysis = ReviewAnalysis.query.filter_by(product_id=pid).first()

    specs = {}
    try:
        specs = json.loads(product.specs) if product.specs else {}
    except (json.JSONDecodeError, TypeError):
        pass

    images = []
    try:
        images = json.loads(product.images) if product.images else []
    except (json.JSONDecodeError, TypeError):
        pass

    neg_reviews = [r for r in reviews if r.rating <= 3]
    pos_reviews = [r for r in reviews if r.rating >= 4]
    mid_reviews = [r for r in reviews if r.rating == 3]

    rating_dist = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        if r.rating in rating_dist:
            rating_dist[r.rating] += 1

    return render_template("product.html",
                           product=product, reviews=reviews,
                           neg_reviews=neg_reviews, pos_reviews=pos_reviews,
                           mid_reviews=mid_reviews,
                           related=related, analysis=analysis,
                           specs=specs, images=images, rating_dist=rating_dist,
                           has_ai=deepseek_client is not None)


@app.route("/api/product/<pid>/analyze", methods=["POST"])
def api_analyze_reviews(pid):
    """Use AI to analyze negative reviews → product improvement suggestions."""
    if deepseek_client is None:
        return jsonify({"success": False, "error": "未配置 API Key"})

    # Check if analysis already exists
    existing = ReviewAnalysis.query.filter_by(product_id=pid).first()
    if existing:
        return jsonify({"success": True, "analysis": existing.analysis_text})

    reviews = Review.query.filter_by(product_id=pid).order_by(Review.rating).all()
    neg_reviews = [r for r in reviews if r.rating <= 3]
    if not neg_reviews:
        return jsonify({"success": True, "analysis": "暂无差评数据。"})

    # Build prompt from negative reviews
    texts = []
    for r in neg_reviews[:10]:
        body = r.body or r.title or ""
        texts.append(f"[{r.rating}★] {body[:300]}")

    prompt = (
        "You are a product manager. Analyze these negative reviews from Walmart customers "
        "and give specific product improvement suggestions.\n\n"
        "Required output format:\n"
        "## 必须修复的缺陷\n"
        "- 问题描述 | 优先级(P0/P1/P2) | 改进建议\n\n"
        "## 建议改进\n"
        "- 改进点 | 说明\n\n"
        "## 总结\n"
        "- 一句话总结核心问题\n\n"
        "Review data:\n" + "\n---\n".join(texts)
    )

    try:
        resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, max_tokens=2048,
        )
        analysis_text = resp.choices[0].message.content

        # Save to DB
        new_analysis = ReviewAnalysis(product_id=pid, analysis_text=analysis_text)
        db.session.add(new_analysis)
        db.session.commit()

        return jsonify({"success": True, "analysis": analysis_text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/reviews/<pid>")
def api_reviews(pid):
    page = request.args.get("page", 1, type=int)
    per_page = 20
    rating_filter = request.args.get("rating", "all")
    sort = request.args.get("sort", "date")

    q = Review.query.filter_by(product_id=pid)
    if rating_filter == "negative":
        q = q.filter(Review.rating <= 3)
    elif rating_filter == "positive":
        q = q.filter(Review.rating >= 4)
    elif rating_filter == "mid":
        q = q.filter(Review.rating == 3)

    if sort == "helpful":
        q = q.order_by(Review.helpful_count.desc())
    elif sort == "rating_asc":
        q = q.order_by(Review.rating)
    else:
        q = q.order_by(Review.date.desc())

    total = q.count()
    reviews = q.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "reviews": [{
            "id": r.id, "rating": r.rating, "title": r.title,
            "body": r.body[:500], "date": r.date,
            "helpful": r.helpful_count, "verified": r.verified,
            "user": r.user_nickname,
        } for r in reviews],
        "total": total,
        "page": page,
        "pages": (total + per_page - 1) // per_page,
    })


@app.route("/analysis")
def analysis_page():
    products = Product.query.order_by(Product.created_at.desc()).all()
    for p in products:
        total = Review.query.filter_by(product_id=p.product_id).count()
        neg = Review.query.filter_by(product_id=p.product_id).filter(Review.rating <= 3).count()
        p.neg_percent = round(neg / total * 100, 1) if total else 0
    categories = sorted(set(p.category for p in products if p.category))
    brands = sorted(set(p.brand for p in products if p.brand))
    return render_template("analysis.html", products=products,
                           categories=categories, brands=brands)


@app.route("/api/product/<pid>/delete", methods=["POST"])
def api_delete_product(pid):
    """Delete a product and all its associated data."""
    product = Product.query.filter_by(product_id=pid).first()
    if not product:
        return jsonify({"success": False, "error": "产品不存在"})

    try:
        Review.query.filter_by(product_id=pid).delete()
        RelatedProduct.query.filter_by(product_id=pid).delete()
        ReviewAnalysis.query.filter_by(product_id=pid).delete()
        db.session.delete(product)
        db.session.commit()

        # Also remove cached JSON files
        import glob
        for f in glob.glob(os.path.join(basedir, "output", f"*{pid}*")):
            os.remove(f)

        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
