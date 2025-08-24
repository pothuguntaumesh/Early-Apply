from playwright.async_api import async_playwright
import json, re, asyncio

NEXT_RE = re.compile(r'__NEXT_DATA__"\s*type="application/json">(.*?)</script>', re.S)

async def refresh_uber_build_id():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page    = await browser.new_page()
        await page.goto("https://www.uber.com/us/en/careers/list/")
        html    = await page.content()

        m = NEXT_RE.search(html)
        data = json.loads(m.group(1)) if m else {}
        build_id = data.get("buildId")
        first_batch = data.get("props", {}).get("pageProps", {}).get("jobs", [])

        print("Uber build-ID:", build_id)
        print("First batch:", len(first_batch), "jobs")

        await browser.close()
        return build_id, first_batch

if __name__ == "__main__":
    asyncio.run(refresh_uber_build_id())
