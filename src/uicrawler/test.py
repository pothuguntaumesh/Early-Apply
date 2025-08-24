# import asyncio
# import json
# from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
# from crawl4ai.extraction_strategy import LLMExtractionStrategy
# from pydantic import BaseModel, Field
# from typing import List, Optional
# import os
from src.crawler.adapters.uber import UberAdapter
import asyncio


# class JobPosting(BaseModel):
#     jobId: Optional[str] = Field(default="", description="Unique job identifier")
#     title: str = Field(..., description="Job title")
#     companyName: str = Field(..., description="Company name")
#     locationCity: Optional[str] = Field(default="", description="City location")
#     locationCountry: Optional[str] = Field(default="", description="Country location")
#     url: str = Field(..., description="Job application URL")

# async def crawl_careers_page(url: str) -> List[dict]:
#     """
#     Simple careers page crawler - let Crawl4AI do the heavy lifting!
#     """
    
#     # Minimal configuration - let Crawl4AI figure it out
#     browser_config = BrowserConfig(
#         headless=True,
#         viewport_width=1920,
#         viewport_height=1080
#     )
    
#     # Simple run config - just enable scrolling and use LLM for extraction
#     llm_config = LLMConfig(
#         provider="openai/gpt-4o-mini", 
#         api_token=os.getenv("OPENAI_API_KEY")  # Make sure to set this
#     )
    
#     extraction_strategy = LLMExtractionStrategy(
#         llm_config=llm_config,
#         schema=JobPosting.model_json_schema(),
#         extraction_type="schema",
#         instruction="""
#         Extract ALL job postings from this careers page. 
#         For each job, extract:
#         - jobId: any unique identifier (from URL, data attributes, etc.)
#         - title: the job title
#         - companyName: the company name 
#         - locationCity: the city where the job is located
#         - locationCountry: the country where the job is located
#         - url: the link to apply or view more details about the job
        
#         Return ALL jobs you can find on the page as a JSON array.
#         """,
#         chunk_token_threshold=8000,
#         apply_chunking=True,
#         input_format="markdown"  # Let it work with clean markdown
#     )
    
#     run_config = CrawlerRunConfig(
#         cache_mode=CacheMode.BYPASS,
#         extraction_strategy=extraction_strategy,
#         scan_full_page=True,  # Auto-scroll to load everything
#         page_timeout=60000,   # Give it time
#         verbose=True
#     )
    
#     async with AsyncWebCrawler(config=browser_config) as crawler:
#         print(f"🚀 Crawling: {url}")
#         print("🤖 Letting Crawl4AI's LLM figure out the job extraction...")
        
#         result = await crawler.arun(url=url, config=run_config)
        
#         if not result.success:
#             print(f"❌ Failed: {result.error_message}")
#             return []
        
#         print(f"✅ Success! Page: {result.metadata.get('title', 'N/A') if result.metadata else 'N/A'}")
        
#         if result.extracted_content:
#             try:
#                 jobs = json.loads(result.extracted_content)
#                 print(f"🎯 LLM extracted {len(jobs)} jobs")
#                 return jobs
#             except json.JSONDecodeError as e:
#                 print(f"⚠️ JSON decode error: {e}")
#                 print("Raw extracted content:", result.extracted_content[:500])
#                 return []
#         else:
#             print("⚠️ No extracted content found")
#             return []

# async def main():
#     # Just give it the URL and let it work!
#     careers_url = "https://www.uber.com/us/en/careers/list"
    
#     jobs = await crawl_careers_page(careers_url)
    
#     # Display results
#     print("\n" + "="*60)
#     print("🎯 EXTRACTED JOB POSTINGS")
#     print("="*60)
    
#     for i, job in enumerate(jobs, 1):
#         print(f"\n{i}. {job.get('title', 'N/A')}")
#         print(f"   Company: {job.get('companyName', 'N/A')}")
#         print(f"   Location: {job.get('locationCity', 'N/A')}, {job.get('locationCountry', 'N/A')}")
#         print(f"   URL: {job.get('url', 'N/A')}")
#         print(f"   ID: {job.get('jobId', 'N/A')}")
    
#     # Save results
#     with open('jobs.json', 'w', encoding='utf-8') as f:
#         json.dump(jobs, f, indent=2, ensure_ascii=False)
    
#     print(f"\n💾 Saved {len(jobs)} job postings to jobs.json")

# if __name__ == "__main__":
#     asyncio.run(main())
