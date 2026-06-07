#!/usr/bin/env python3
"""Fetch ALL reviews from Walmart reviews listing page (paginated)."""
import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curl_cffi import requests

def fetch_all_reviews(pid: str, max_pages: int = 10):
    """Paginate through Walmart reviews page and collect all reviews."""
    s = requests.Session()
    s.get("https://www.walmart.com", impersonate="safari17_0", timeout=15)

    all_reviews = []
    total = 0

    for page in range(1, max_pages + 1):
        url = f"https://www.walmart.com/reviews/product/{pid}?page={page}&limit=20&sort=recency"
        print(f"  Page {page}...", end=" ", flush=True)

        try:
            resp = s.get(url, impersonate="safari17_0", timeout=30)
        except Exception as e:
            print(f"TIMEOUT: {e}")
            time.sleep(5)
            try:
                resp = s.get(url, impersonate="safari17_0", timeout=30)
            except:
                print("  Retry failed, stopping")
                break

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            print("No Next.js data found")
            break

        nd = json.loads(m.group(1))
        rv = nd.get("props",{}).get("pageProps",{}).get("initialData",{}).get("data",{}).get("reviews",{})

        if not isinstance(rv, dict):
            print("No reviews data")
            break

        total = rv.get("totalReviewCount", total)
        batch = rv.get("customerReviews", [])

        if not batch:
            print("Empty page, done")
            break

        all_reviews.extend(batch)
        print(f"{len(batch)} reviews (total: {len(all_reviews)}/{total})")

        if len(batch) < 20:
            break

        time.sleep(2)

    # Sort by rating
    neg = [r for r in all_reviews if r.get("rating", 5) <= 3]
    pos = [r for r in all_reviews if r.get("rating", 0) > 3]
    neg.sort(key=lambda x: (x.get("rating",5), -(x.get("positiveFeedback",0) or 0)))
    pos.sort(key=lambda x: (-x.get("rating",0), -(x.get("positiveFeedback",0) or 0)))

    return {
        "total_reviews": total or len(all_reviews),
        "all_reviews": all_reviews,
        "negative_reviews": neg,
        "positive_reviews": pos,
    }


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "5273768931"
    print(f"Fetching all reviews for product {pid}...")
    result = fetch_all_reviews(pid)
    print(f"\nDone! Total: {result['total_reviews']}")
    print(f"  Negative (1-3★): {len(result['negative_reviews'])}")
    print(f"  Positive (4-5★): {len(result['positive_reviews'])}")

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"all_reviews_{pid}.json")
    with open(path, "w") as f:
        json.dump(result, f, ensure_ascii=False, default=str, indent=2)
    print(f"Saved to {path}")
