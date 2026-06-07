import re, json
from curl_cffi import requests

s = requests.Session()
s.get("https://www.walmart.com", impersonate="safari17_0")

# === Search page deep dive ===
resp = s.get("https://www.walmart.com/search?q=sony+headphones", impersonate="safari17_0")
html = resp.text

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if m:
    next_data = json.loads(m.group(1))
    search = next_data["props"]["pageProps"]["initialData"]["searchResult"]

    # itemStacks
    stacks = search.get("itemStacks", [])
    print(f"itemStacks count: {len(stacks)}")
    for i, stack in enumerate(stacks[:2]):
        print(f"\nStack {i} keys: {list(stack.keys())}")
        items = stack.get("items", [])
        print(f"  Items: {len(items)}")
        if items:
            print(f"  First item keys: {list(items[0].keys()) if isinstance(items[0], dict) else type(items[0])}")
            print(f"  First item name: {items[0].get('name','?')}")
            print(f"  First item price: {items[0].get('price','?')}")

    # Also check pagination
    pag = search.get("paginationV2", {})
    print(f"\nPagination: {json.dumps(pag, ensure_ascii=False)[:200]}")

    # Check modules
    mods = search.get("modules", {})
    print(f"\nModules keys: {list(mods.keys())[:10]}")


# === Product detail page deep dive ===
print("\n\n=== PRODUCT DETAIL ===")
pid = "19074250200"
resp2 = s.get(f"https://www.walmart.com/ip/{pid}", impersonate="safari17_0")
html2 = resp2.text

m2 = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html2, re.DOTALL)
if m2:
    pd = json.loads(m2.group(1))
    print(f"Page query: {pd.get('query', {})}")
    props = pd.get("props", {}).get("pageProps", {})
    print(f"pageProps keys: {list(props.keys())[:20]}")

    # Check initialData
    init = props.get("initialData", {})
    print(f"initialData keys: {list(init.keys())[:20]}")

    product_data = init.get("product", {}) or props.get("product", {})
    print(f"\nProduct data type: {type(product_data)}")
    if isinstance(product_data, dict):
        # Check all sections
        for key in ["priceInfo", "name", "brand", "averageRating", "numberOfReviews",
                     "imageInfo", "description", "specifications", "availability"]:
            val = product_data.get(key)
            if val:
                print(f"  {key}: {str(val)[:100]}")

        print(f"\nProduct top keys: {list(product_data.keys())[:30]}")
else:
    print(f"Status: {resp2.status_code}, URL: {resp2.url}")
