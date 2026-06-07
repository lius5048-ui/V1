from crewai import Task

from agents import coordinator, crawler, extractor, auditor


analyze_request = Task(
    description=(
        "Analyze the crawled Walmart product data and understand what we have.\n\n"
        "Crawled data: {crawl_data}\n\n"
        "Review the JSON data and output a brief analysis of what was collected, "
        "including: the main product, its key specs, how many reviews were found, "
        "how many related products were discovered."
    ),
    expected_output="Brief analysis of the crawled data structure",
    agent=coordinator,
)


extract_and_analyze = Task(
    description=(
        "You are given full crawled Walmart product data including details, reviews, "
        "and related products. Produce a comprehensive markdown report.\n\n"
        "Crawled data: {crawl_data}\n\n"
        "Write a report with ALL of the following sections:\n\n"
        "## Product Information\n"
        "- Title, Brand, Price, Currency\n"
        "- SKU / Product ID\n"
        "- Rating, Total Review Count\n"
        "- Availability\n"
        "- Full Description\n"
        "- Key Specifications (as a bullet list)\n"
        "- Image URLs\n\n"
        "## Related Products\n"
        "- Table of related products with Name, Price, Rating, Review Count\n\n"
        "## Review Analysis (CRITICAL - most important section)\n"
        "### Negative Reviews Detail\n"
        "List EVERY negative review (rating 1-3) in a numbered list with:\n"
        "- Rating, Title, Full review text, Date, Helpful count, Verified purchase\n\n"
        "### Negative Topics Summary\n"
        "Group negative reviews into themes:\n"
        "- Product quality / defects\n"
        "- Sizing / fit issues\n"
        "- Shipping / delivery problems\n"
        "- Customer service\n"
        "- Value for money\n"
        "- Other\n"
        "For each theme: count, representative quotes, severity\n\n"
        "### Positive Summary\n"
        "What customers liked most, with supporting quotes\n\n"
        "### Overall Verdict\n"
        "Balanced assessment based on ALL available review data\n\n"
        "IMPORTANT RULES:\n"
        "- Do NOT skip any negative review - list them ALL\n"
        "- Use actual review text, not summaries\n"
        "- Write in clean markdown\n"
        "- If there are no negative reviews, state that explicitly"
    ),
    expected_output="Complete markdown report with all sections filled",
    agent=extractor,
)


quality_audit = Task(
    description=(
        "Review the report from the previous step for quality and completeness.\n\n"
        "Check:\n"
        "1. Are ALL sections present? (Product Info, Related Products, Negative Reviews, "
        "Negative Topics, Positive Summary, Overall Verdict)\n"
        "2. Are negative reviews listed with full text, not just summaries?\n"
        "3. Are there duplicate entries in Related Products?\n"
        "4. Is price/rating/availability populated?\n"
        "5. Is the overall assessment balanced?\n\n"
        "Add a quality score (0-100) and list any issues. "
        "Return the COMPLETE report with quality annotations at the end."
    ),
    expected_output="Final report with quality score appended",
    agent=auditor,
    context=[extract_and_analyze],
)
