import json

with open("/home/nihao/walmart-crawler/tools/output/all_reviews_5273768931.json") as f:
    data = json.load(f)

all_r = data.get("all_reviews", [])
print(f"Total reviews: {len(all_r)}")

for i, r in enumerate(all_r[:100]):
    rating_val = r.get("rating", "?")
    helpful = r.get("helpful_count", r.get("positiveFeedback", 0))
    title = r.get("reviewTitle", r.get("title", ""))
    text = r.get("reviewText", r.get("body", r.get("text", "")))

    print(f"\n--- #{i+1} | {rating_val}★ | helpful={helpful} ---")
    print(f"  Title: {str(title)[:100] if title else '(empty)'}")
    print(f"  Body ({len(str(text))} chars): {str(text)[:200]}")
