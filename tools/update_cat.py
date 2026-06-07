import sys, os, json
sys.path.insert(0, "/home/nihao/walmart-crawler")

from tools.walmart_crawler import fetch_product_details

# Update cached JSON for 10928125 with category
path = "/home/nihao/walmart-crawler/output/crawl_10928125.json"
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)

    d = fetch_product_details("10928125")
    new_cat = d.get("category", "")
    print(f"New category: {new_cat}")

    data["details"]["category"] = new_cat
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    print(f"Updated {path}")

# Now import it
from import_data import import_json
from app import app, db

with app.app_context():
    import_json(path)
    print("Import done")
