import json, sys

sys.path.insert(0, "/home/nihao/walmart-crawler")
from config import deepseek_client

with open("/home/nihao/walmart-crawler/output/crawl_10928125.json") as f:
    data = json.load(f)

neg = data["reviews"]["negative_reviews"]
print(f"Client available: {deepseek_client is not None}")
print(f"Negative reviews: {len(neg)}")

if deepseek_client:
    texts = []
    for r in neg[:8]:
        rating_val = r.get("rating", "?")
        body = r.get("reviewText", r.get("body", ""))
        texts.append(f"[{rating_val}★] {body[:300]}")

    prompt = "You are a product manager. Analyze these negative reviews and give product improvement suggestions. Identify must-fix defects and priorities. Keep it concise.\n\n" + "\n---\n".join(texts)
    resp = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":prompt}],
        temperature=0.1, max_tokens=1024,
    )
    print("\n=== AI Analysis ===")
    print(resp.choices[0].message.content)
else:
    print("\nNo API Key — can only show raw reviews, no AI analysis.")
    print("But you can still read all 68 negative reviews manually")
    print("and make your own judgement about what to improve.")
