from crewai import Crew, Process

from agents import coordinator, extractor, auditor
from tasks import analyze_request, extract_and_analyze, quality_audit

crew = Crew(
    agents=[coordinator, extractor, auditor],
    tasks=[
        analyze_request,
        extract_and_analyze,
        quality_audit,
    ],
    process=Process.sequential,
    verbose=True,
)
