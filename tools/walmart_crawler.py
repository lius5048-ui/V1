import re
import json
import time
import random
import logging
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


def _get_session():
    """Create a curl_cffi session with Safari impersonation to bypass Walmart anti-bot."""
    from curl_cffi import requests
    s = requests.Session()
    s.get("https://www.walmart.com", impersonate="safari17_0")
    return s


def _extract_next_data(html: str) -> Optional[dict]:
    """Extract __NEXT_DATA__ JSON from Walmart page HTML."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    return None


def _extract_product_id(url_or_id: str) -> str:
    """Extract Walmart product ID from URL or return as-is."""
    if url_or_id.isdigit():
        return url_or_id
    m = re.search(r'/ip/(\d+)(?:\?|/|$)', url_or_id)
    if m:
        return m.group(1)
    raise ValueError(f"Cannot extract product ID from: {url_or_id}")


def search_products(keyword: str, limit: int = 20) -> list[dict]:
    """Search Walmart for products matching a keyword. Uses Next.js data."""
    url = f"https://www.walmart.com/search?q={quote(keyword)}"
    logger.info(f"Searching Walmart for: {keyword}")

    s = _get_session()
    resp = s.get(url, impersonate="safari17_0")
    html = resp.text

    products = []
    next_data = _extract_next_data(html)
    if not next_data:
        logger.warning("No __NEXT_DATA__ found in search page")
        return products

    try:
        search_result = next_data["props"]["pageProps"]["initialData"]["searchResult"]
        item_stacks = search_result.get("itemStacks", [])
        for stack in item_stacks:
            items = stack.get("items", [])
            for item in items:
                if len(products) >= limit:
                    break
                p = _parse_search_item(item)
                if p:
                    products.append(p)

        # Sort by review_count descending (most reviewed first)
        products.sort(key=lambda x: x.get("review_count", 0), reverse=True)
    except (KeyError, TypeError) as e:
        logger.warning(f"Error parsing search data: {e}")

    logger.info(f"Found {len(products)} products for keyword '{keyword}'")
    return products[:limit]


def _parse_search_item(item: dict) -> Optional[dict]:
    """Parse a single product from search item data."""
    try:
        pid = item.get("usItemId", item.get("id", ""))
        if not pid:
            return None

        price_info = item.get("priceInfo", {}) or {}
        if isinstance(price_info, list):
            price_info = price_info[0] if price_info else {}
        image_info = item.get("imageInfo", {}) or {}
        rating = item.get("averageRating") or item.get("rating")
        if isinstance(rating, dict):
            rating = rating.get("averageRating")

        return {
            "product_id": str(pid),
            "title": (item.get("name", "") or "").strip(),
            "price": (price_info.get("currentPrice", {}).get("price")
                      if isinstance(price_info.get("currentPrice"), dict)
                      else price_info.get("currentPrice")
                      or price_info.get("price")
                      or item.get("price")),
            "currency": "USD",
            "brand": item.get("brand", "") or "",
            "rating": rating,
            "review_count": (item.get("numberOfReviews")
                             or item.get("reviewCount", 0)),
            "availability": item.get("availabilityStatusV2", ""),
            "url": f"https://www.walmart.com/ip/{pid}",
            "image": image_info.get("url", ""),
        }
    except Exception as e:
        logger.warning(f"Error parsing search item: {e}")
        return None


def fetch_product_details(url_or_id: str) -> dict:
    """Fetch full product details from product page using Next.js data."""
    product_id = _extract_product_id(url_or_id)
    if url_or_id.isdigit():
        url = f"https://www.walmart.com/ip/{product_id}"
    else:
        url = url_or_id

    logger.info(f"Fetching product details: {url}")

    s = _get_session()
    resp = s.get(url, impersonate="safari17_0")
    html = resp.text

    result = {
        "product_id": product_id,
        "url": str(resp.url),
        "title": "",
        "price": None,
        "currency": "USD",
        "brand": "",
        "sku": "",
        "rating": None,
        "review_count": 0,
        "availability": "",
        "description": "",
        "specs": {},
        "images": [],
    }

    next_data = _extract_next_data(html)
    if not next_data:
        logger.warning("No __NEXT_DATA__ found on product page")
        return result

    try:
        data_wrapper = next_data.get("props", {}).get("pageProps", {}).get("initialData", {}).get("data", {})
        product = data_wrapper.get("product", {}) if isinstance(data_wrapper, dict) else {}
        idml = data_wrapper.get("idml", {}) if isinstance(data_wrapper, dict) else {}

        if product:
            _parse_product_data(product, result)
        if idml:
            _parse_idml_data(idml, result)

        _parse_jsonld(html, result)
    except Exception as e:
        logger.warning(f"Error parsing product page: {e}")

    return result


def _parse_product_data(product: dict, result: dict):
    """Extract product info from Next.js product object."""
    price_info = product.get("priceInfo", {}) or {}
    if isinstance(price_info, list):
        price_info = price_info[0] if price_info else {}
    image_info = product.get("imageInfo", {}) or {}

    result["title"] = product.get("name", product.get("title", ""))
    result["brand"] = product.get("brand", product.get("manufacturerName", ""))
    # Extract category from product page category path
    cat_path = product.get("category", {}).get("path", [])
    result["category"] = cat_path[0].get("name", "") if cat_path else product.get("type", product.get("ironbankCategory", ""))
    result["sku"] = product.get("upc", product.get("sku", product.get("skuId", "")))
    result["rating"] = product.get("averageRating")
    result["review_count"] = product.get("numberOfReviews", 0)
    result["availability"] = (product.get("availabilityStatusV2",
                                product.get("availabilityStatus", "")))
    result["product_id"] = str(product.get("usItemId", result["product_id"]))

    # Price
    current_price = price_info.get("currentPrice", {})
    if isinstance(current_price, dict):
        result["price"] = current_price.get("price", current_price.get("priceString"))
    else:
        result["price"] = current_price or price_info.get("price")

    # Images
    all_images = image_info.get("allImages", []) or []
    if isinstance(all_images, list):
        result["images"] = [img.get("url", img) if isinstance(img, dict) else img
                           for img in all_images if img]
    else:
        primary = image_info.get("primaryImage", image_info.get("url", ""))
        if primary:
            result["images"] = [primary]


def _parse_idml_data(idml: dict, result: dict):
    """Extract description and specs from idml data."""
    # Description
    long_desc = idml.get("longDescription", "")
    short_desc = idml.get("shortDescription", "")
    result["description"] = long_desc or short_desc or ""

    # Specs from productHighlights
    highlights = idml.get("productHighlights", [])
    if isinstance(highlights, list):
        for h in highlights:
            if isinstance(h, dict):
                name = h.get("name", "")
                value = h.get("value", "")
                if name and value:
                    result["specs"][name] = value


def _parse_jsonld(html: str, result: dict):
    """Supplement missing data from JSON-LD."""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    _apply_ld(item, result)
        except json.JSONDecodeError:
            continue


def _apply_ld(data: dict, result: dict):
    """Apply JSON-LD fields if not already set."""
    if not result["title"] and data.get("name"):
        result["title"] = data["name"]
    if not result["description"] and data.get("description"):
        result["description"] = data["description"]
    if not result["brand"]:
        brand = data.get("brand", {})
        if isinstance(brand, dict):
            result["brand"] = brand.get("name", "")
    if not result.get("price"):
        offers = data.get("offers", {})
        if isinstance(offers, dict):
            result["price"] = offers.get("price")
    if not result.get("sku") and data.get("sku"):
        result["sku"] = data["sku"]


def _extract_reviews_from_page(product_id: str) -> Optional[dict]:
    """Extract reviews embedded in the product page's Next.js data."""
    s = _get_session()
    url = f"https://www.walmart.com/ip/{product_id}"
    resp = s.get(url, impersonate="safari17_0")
    html = resp.text
    next_data = _extract_next_data(html)
    if not next_data:
        return None
    try:
        reviews_data = next_data["props"]["pageProps"]["initialData"]["data"]["reviews"]
        return reviews_data
    except (KeyError, TypeError):
        return None


def fetch_product_reviews(product_id: str, max_reviews: int = 500) -> dict:
    """Fetch product reviews from Walmart. Uses page-embedded data first, then attempts API fetch."""
    pid = _extract_product_id(product_id)
    logger.info(f"Fetching reviews for product {pid}, max={max_reviews}")

    all_reviews = []
    total_count = 0
    avg_rating = None

    # Step 1: Extract reviews from product page Next.js data
    page_data = _extract_reviews_from_page(pid)
    if page_data:
        total_count = page_data.get("totalReviewCount", 0)
        avg_rating = page_data.get("averageOverallRating")

        # Get embedded customer reviews
        customer_reviews = page_data.get("customerReviews", [])
        for rv in customer_reviews:
            if isinstance(rv, dict):
                all_reviews.append(_parse_review(rv))

        logger.info(f"Got {len(all_reviews)} reviews from page data (total={total_count})")

    # Step 2: Try fetching more reviews via API (pagination)
    # Product page session might have better cookies for API access
    if len(all_reviews) < max_reviews and total_count > len(all_reviews):
        try:
            more_reviews = _fetch_reviews_via_api(pid, offset=len(all_reviews), max_reviews=max_reviews)
            existing_ids = {r.get("title", "") + r.get("body", "")[:50] for r in all_reviews}
            for rv in more_reviews:
                key = rv.get("title", "") + rv.get("body", "")[:50]
                if key not in existing_ids:
                    all_reviews.append(rv)
                    existing_ids.add(key)
        except Exception as e:
            logger.warning(f"API review fetch failed (non-critical): {e}")

    # Separate negative (<=3) and positive (>3) reviews
    negative = [r for r in all_reviews if r["rating"] <= 3]
    negative.sort(key=lambda x: x["helpful_count"], reverse=True)
    positive = [r for r in all_reviews if r["rating"] > 3]
    positive.sort(key=lambda x: x["helpful_count"], reverse=True)

    return {
        "total_reviews": total_count or len(all_reviews),
        "main_product_rating": avg_rating,
        "all_reviews": all_reviews,
        "negative_reviews": negative,
        "positive_reviews": positive,
    }


def _parse_review(rv: dict) -> dict:
    """Normalize a review dict from various Walmart formats."""
    helpful = rv.get("helpfulCount", rv.get("helpfulVotes", rv.get("positiveFeedback", 0)))
    return {
        "rating": rv.get("rating", rv.get("overallRating", 0)),
        "title": rv.get("title", rv.get("reviewTitle", "")),
        "body": rv.get("reviewText", rv.get("reviewBody", rv.get("text", ""))),
        "date": rv.get("datePosted", rv.get("submissionDate", rv.get("reviewSubmissionTime", ""))),
        "helpful_count": helpful if isinstance(helpful, (int, float)) else 0,
        "verified_purchase": rv.get("verifiedPurchaser", rv.get("verified", False)),
        "user_nickname": rv.get("userNickname", ""),
    }


def _fetch_reviews_via_api(pid: str, offset: int = 0, max_reviews: int = 500) -> list[dict]:
    """Attempt to fetch additional reviews via Walmart API with session cookies."""
    from curl_cffi import requests

    s = _get_session()
    # First visit the product page to establish cookies
    s.get(f"https://www.walmart.com/ip/{pid}", impersonate="safari17_0")

    all_reviews = []
    page = (offset // 20) + 1
    attempts = 0
    max_pages = 10

    while len(all_reviews) < max_reviews - offset and page <= max_pages and attempts < 3:
        try:
            # Try multiple API endpoints
            urls = [
                f"https://www.walmart.com/global/api/product/{pid}/reviews?page={page}&limit=20&sort=recency",
                f"https://www.walmart.com/product/{pid}/reviews?page={page}&limit=20&sort=recency",
            ]

            data = None
            for url in urls:
                resp = s.get(url, impersonate="safari17_0",
                             headers={"Accept": "application/json, text/plain, */*",
                                      "Referer": f"https://www.walmart.com/ip/{pid}",
                                      "Origin": "https://www.walmart.com"})
                content = resp.text.strip()
                if content and not content.startswith("<!DOCTYPE") and not content.startswith("<html"):
                    try:
                        data = resp.json()
                        if isinstance(data, dict) and ("reviews" in data or "customerReviews" in data):
                            break
                    except json.JSONDecodeError:
                        continue

            if not data:
                attempts += 1
                time.sleep(random.uniform(2, 4))
                continue

            reviews = (data.get("reviews", [])
                       or data.get("customerReviews", [])
                       or data.get("items", []))
            review_list = data.get("reviewList", {})
            if isinstance(review_list, dict) and not reviews:
                reviews = review_list.get("reviews", [])

            if not reviews:
                break

            for rv in reviews:
                if isinstance(rv, dict):
                    all_reviews.append(_parse_review(rv))

            if len(reviews) < 20:
                break
            page += 1
            time.sleep(random.uniform(2.0, 4.0))
            attempts = 0

        except Exception as e:
            logger.warning(f"Reviews API error (page {page}): {e}")
            attempts += 1
            time.sleep(random.uniform(2, 4))

    return all_reviews
