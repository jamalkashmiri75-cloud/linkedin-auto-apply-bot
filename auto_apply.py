# auto_apply.py
import os, time, random, sys
from playwright.sync_api import sync_playwright

# Load credentials from GitHub Secrets / Environment
EMAIL = os.getenv("jamalkashmiri52@gmail.com")
PASSWORD = os.getenv("jamalch622")
RESUME_PATH = os.getenv("RESUME_PATH", "resume.pdf")

# Job categories (keywords)
JOB_KEYWORDS = ["WordPress", "PHP", "Java", "Virtual Assistant", "CSS", "HTML"]
JOB_LOCATION = os.getenv("JOB_LOCATION", "Pakistan")

# Jobs per category
JOBS_PER_CATEGORY = int(os.getenv("JOBS_PER_CATEGORY", "10"))

if not EMAIL or not PASSWORD:
    print("❌ Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD as environment variables.")
    sys.exit(1)

def human_pause(a=1.0, b=2.5):
    """Random pause to look human-like"""
    time.sleep(a + random.random() * b)

def login(page):
    page.goto("https://www.linkedin.com/login", wait_until="networkidle")
    page.fill('input#username', EMAIL)
    page.fill('input#password', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("✅ Logged in")

def search_job_links(page, keyword, location, max_links=20):
    q = keyword.strip().replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={location.replace(' ', '%20')}&f_AL=true&f_TPR=r86400"
    print(f"\n🔎 Searching jobs: {keyword} in {location}")
    page.goto(url, wait_until="networkidle")
    human_pause(1.5, 2.5)

    anchors = page.query_selector_all("a[href*='/jobs/view/']")
    links = []
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/jobs/view/" in href:
            full = href if href.startswith("http") else "https://www.linkedin.com" + href
            if full not in links:
                links.append(full)

    print(f"   Found {len(links)} jobs (taking {min(len(links), max_links)})")
    return links[:max_links]

def try_easy_apply(page, job_url):
    print("➡️ Visiting", job_url)
    page.goto(job_url, wait_until="networkidle")
    human_pause(1.0, 2.0)

    try:
        ea = page.locator("button:has-text('Easy Apply')").first
        if not ea or not ea.is_visible():
            print("   ❌ No Easy Apply found")
            return False
        ea.click()
        human_pause(1.0, 1.5)
    except Exception as e:
        print("   ⚠️ Easy Apply click error:", e)
        return False

    # Upload resume
    try:
        file_input = page.query_selector("input[type='file']")
        if file_input:
            file_input.set_input_files(RESUME_PATH)
            human_pause(0.8, 1.2)
    except Exception as e:
        print("   ⚠️ File upload error:", e)

    # Handle multi-step modal
    for step in range(8):
        human_pause(0.8, 1.5)

        if page.locator("button:has-text('Submit')").count() > 0:
            page.locator("button:has-text('Submit')").first.click()
            print("   ✅ Submitted application")
            return True

        if page.locator("button:has-text('Done')").count() > 0:
            page.locator("button:has-text('Done')").first.click()
            print("   ✅ Finished application")
            return True

        if page.locator("button:has-text('Next')").count() > 0:
            page.locator("button:has-text('Next')").first.click()
            continue

        if page.locator("button:has-text('Continue')").count() > 0:
            page.locator("button:has-text('Continue')").first.click()
            continue

        if page.locator("button[aria-label*='submit application' i]").count() > 0:
            page.locator("button[aria-label*='submit application' i]").first.click()
            print("   ✅ Submitted via aria-label")
            return True

        break

    print("   ⚠️ Could not finish Easy Apply")
    return False

def main():
    total_applied = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()

        login(page)

        for keyword in JOB_KEYWORDS:
            applied_this_category = 0
            links = search_job_links(page, keyword, JOB_LOCATION, max_links=30)

            for link in links:
                if applied_this_category >= JOBS_PER_CATEGORY:
                    break
                try:
                    if try_easy_apply(page, link):
                        applied_this_category += 1
                        total_applied += 1
                        print(f"   Applied {applied_this_category}/{JOBS_PER_CATEGORY} in {keyword}")
                    human_pause(3.0, 5.0)
                except Exception as e:
                    print("   ⚠️ Error:", e)

        print(f"\n🎉 Done. Applied to {total_applied} jobs today.")
        context.close()
        browser.close()

if __name__ == "__main__":
    main()
