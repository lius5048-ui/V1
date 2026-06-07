import sys, os, json
sys.path.insert(0, "/home/nihao/walmart-crawler")
from tools.walmart_crawler import fetch_product_details, search_products

d = fetch_product_details("10928125")
print("Category:", d.get("category", ""))
print("Title:", d.get("title", "")[:60])
