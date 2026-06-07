import re, json
from curl_cffi import requests

s = requests.Session()
s.get("https://www.walmart.com", impersonate="safari17_0")

pid = "5273768931"
resp = s.get(f"https://www.walmart.com/ip/{pid}", impersonate="safari17_0")
html = resp.text

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
nd = json.loads(m.group(1))
data = nd["props"]["pageProps"]["initialData"]["data"]

# Check reviews data embedded in page
review_data = data.get("reviews", {})
print(f"Reviews data type: {type(review_data)}")
if isinstance(review_data, dict):
    print(f"Keys: {list(review_data.keys())}")
    print(f"averageOverallRating: {review_data.get('averageOverallRating')}")
    print(f"totalReviewCount: {review_data.get('totalReviewCount')}")

    # Check if reviews list exists
    for k in ["reviews", "reviewList", "customerReviews", "items", "topNegative", "topPositive"]:
        v = review_data.get(k)
        if v:
            print(f"\nreview_data['{k}']: type={type(v)}")
            if isinstance(v, list):
                if v:
                    print(f"  len={len(v)}")
                    if isinstance(v[0], dict):
                        print(f"  first item keys: {list(v[0].keys())[:15]}")
                        print(f"  first review text: {v[0].get('reviewText', v[0].get('text',''))[:100]}")
            elif isinstance(v, dict):
                print(f"  nested keys: {list(v.keys())[:10]}")

# Also look for reviews in the entire page HTML (SSR rendered)
print("\n\n=== Search for review-like data in HTML ===")
review_count = len(re.findall(r'class="review-text"', html))
print(f"review-text classes: {review_count}")

# Look for review data JSON embedded in page
for pattern in [
    r'"reviewText":"([^"]+)"',
    r'"reviewBody":"([^"]+)"',
    r'"rating":(\d\.?\d*),"title":".*?reviewTitle"',
]:
    matches = re.findall(pattern, html)[:5]
    if matches:
        print(f"Pattern '{pattern[:30]}': {matches[:2]}")

# Check for localStorage/window data in scripts
for pattern in [
    r'window\.__PRELOADED_STATE__\s*=',
    r'window\.__INITIAL_STATE__\s*=',
    r'window\.__DATA__\s*=',
]:
    m = re.search(pattern, html)
    print(f"Has '{pattern[:30]}': {bool(m)}")

# Check if product reviews are fetched client-side via GraphQL
gql = re.findall(r'graphql|gql', html, re.IGNORECASE)
print(f"GraphQL mentions: {len(gql)}")
