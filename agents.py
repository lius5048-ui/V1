from crewai import Agent
from config import deepseek_llm, ollama_llm
from tools import walmart_crawler as wc
import json
import os

OUTPUT_DIR = "/home/nihao/walmart-crawler/output"


def _save_output(filename: str, data):
    """Save crawled data to a JSON file for reliable inter-agent passing."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    return path


coordinator = Agent(
    role="Walmart Crawl Strategist",
    goal="Analyze user requests and design the optimal crawling strategy",
    backstory=(
        "You are an expert at understanding what product data users need from Walmart.com. "
        "You analyze the user's request, determine whether it's a product URL or a search keyword, "
        "and create a clear plan for what data to collect including the main product, "
        "related products, and all reviews (especially negative ones). "
        "Always output your analysis as valid JSON."
    ),
    llm=deepseek_llm,
    verbose=True,
    allow_delegation=False,
)

crawler = Agent(
    role="Web Data Collector",
    goal="Fetch Walmart product data using the provided tools",
    backstory=(
        "You are a web scraper. You use tools to search Walmart, fetch product details, "
        "and get customer reviews. You do NOT need to analyze or format the data - "
        "just call the tools and report what was found in a simple sentence."
    ),
    llm=ollama_llm,
    tools=[],
    verbose=True,
    allow_delegation=False,
)

extractor = Agent(
    role="Product Data Analyst",
    goal="Analyze crawled product data and write a comprehensive markdown report",
    backstory=(
        "You are a data analyst specialized in e-commerce analysis. "
        "You read saved JSON data files and produce detailed structured reports. "
        "You excel at extracting insights from customer reviews, identifying common "
        "complaint themes, and writing clear assessments."
    ),
    llm=deepseek_llm,
    verbose=True,
    allow_delegation=False,
)

auditor = Agent(
    role="Data Quality Auditor",
    goal="Verify report completeness and add quality annotations",
    backstory=(
        "You are a meticulous QA specialist. You check every section of a report "
        "for completeness and accuracy. You add quality scores and flag issues."
    ),
    llm=deepseek_llm,
    verbose=True,
    allow_delegation=False,
)
