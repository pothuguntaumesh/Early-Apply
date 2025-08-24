import asyncio
import json
import httpx
from playwright.async_api import async_playwright

GRAPHQL_NAME = "CareersJobSearchResultsDataQuery"
GRAPHQL_URL = "https://www.metacareers.com/api/graphql"
HARDCODED_DOC_ID = "29615178951461218"

async def get_headers_from_browser():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        headers = {}

        async def intercept_request(route, request):
            nonlocal headers
            if request.url.endswith("/api/graphql"):
                if request.headers.get("fb-api-req-friendly-name") == GRAPHQL_NAME:
                    headers = request.headers
                    await route.abort()
                    return
            await route.continue_()

        await page.route("**/*", intercept_request)
        await page.goto("https://www.metacareers.com/jobs")
        await page.wait_for_timeout(6000)
        await browser.close()
        return headers

def make_graphql_call(headers):
    payload = {
        "doc_id": HARDCODED_DOC_ID,
        "variables": json.dumps({
            "results_per_page": 25,
            "cursor": None,
            "search_input": {
                "q": None,
                "leadership_levels": [],
                "teams": [],
                "sub_teams": [],
                "roles": [],
                "offices": [],
                "divisions": [],
                "saved_jobs": [],
                "saved_searches": []
            }
        })
    }

    required_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "fb-api-req-friendly-name": GRAPHQL_NAME,
        "cookie": headers.get("cookie", ""),
        "user-agent": headers.get("user-agent", ""),
        "origin": "https://www.metacareers.com",
        "referer": "https://www.metacareers.com/jobs"
    }

    response = httpx.post(GRAPHQL_URL, data=payload, headers=required_headers)
    print("✅ Status:", response.status_code)
    if response.headers.get("content-type", "").startswith("application/json"):
        print(json.dumps(response.json(), indent=2)[:1500])
    else:
        print("❌ Not a JSON response")
        print(response.text[:1000])

async def main():
    print("🎯 Launching browser to get real session headers...")
    headers = await get_headers_from_browser()
    if headers:
        print("✅ Got headers. Now hitting API directly.")
        make_graphql_call(headers)
    else:
        print("❌ Failed to capture headers")

if __name__ == "__main__":
    asyncio.run(main())
