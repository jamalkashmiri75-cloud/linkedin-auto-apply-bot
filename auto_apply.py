# auto_apply.py
import os, time, random, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

EMAIL = os.getenv("jamalkashmiri72@gmail.com")
PASSWORD = os.getenv("jamalch622")
RESUME_PATH = "resume.pdf"
MAX_APPLIES = int(os.getenv("MAX_APPLIES_PER_RUN", "5"))
JOB_KEYWORD = os.getenv("JOB_KEYWORD", "")
JOB_LOCATION = os.getenv("JOB_LOCATION", "")

if not EMAIL or not PASSWORD:
    print("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD as environment variables.")
    sys.exit(1)

def human_pause(a=1.0, b=2.5):
    time.sleep(a + random.random() * b)

def login(page):
    page.goto("https://www.linkedin.com/login", wait_until="networkidle")
    page.fill('input#username', EMAIL)
    page.fill('input#password', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    print("Logged in")

def search_job_links(page, max_links=30):
    if Path("job_links.txt").exists():
        print("Using job_links.txt")
        return [l.strip() for l in open("job_links.txt","r", encoding="utf-8").read().splitlines() if l.strip()][:max_links]

    if not JOB_KEYWORD:
        print("No JOB_KEYWORD and no job_links.txt — nothing to do.")
        return []

    # Build a LinkedIn search URL for "last 24 hours" using f_TPR=r86400 (works commonly)
    q = JOB_KEYWORD.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}&f_TPR=r86400"
    if JOB_LOCATION:
        url += "&location=" + JOB_LOCATION.replace(" ", "%20")
    print("Search URL:", url)
    page.goto(url, wait_until="networkidle")
    human_pause(1.5, 2.0)

    # collect job links
    anchors = page.query_selector_all("a[href*='/jobs/view/']")
    links = []
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/jobs/view/" in href:
            full = href if href.startswith("http") else "https://www.linkedin.com" + href
            if full not in links:
                links.append(full)
    print(f"Found {len(links)} job links (returning up to {max_links})")
    return links[:max_links]

def try_easy_apply(page, job_url):
    print("Visiting", job_url)
    page.goto(job_url, wait_until="networkidle")
    human_pause(1.0, 2.0)
    try:
        ea = page.locator("button:has-text('Easy Apply')").first
        if not ea or not ea.is_visible():
            print("No Easy Apply found")
            return False
        ea.click()
        human_pause(1.0, 1.5)
    except Exception as e:
        print("Easy Apply click error:", e)
        return False

    # upload resume if file input exists
    try:
        file_input = page.query_selector("input[type='file']")
        if file_input:
            file_input.set_input_files(RESUME_PATH)
            human_pause(0.8, 1.2)
    except Exception as e:
        print("File upload error (maybe no upload field):", e)

    # try to progress the modal to final submit
    for step in range(8):
        human_pause(0.8, 1.5)
        # try Submit
        if page.locator("button:has-text('Submit')").count() > 0:
            page.locator("button:has-text('Submit')").first.click()
            human_pause(1.0, 1.5)
            print("Submitted application (or clicked Submit)")
            # close modal if present
            try:
                if page.locator("button[aria-label='Dismiss']").count() > 0:
                    page.locator("button[aria-label='Dismiss']").first.click()
            except:
                pass
            return True
        # try Done
        if page.locator("button:has-text('Done')").count() > 0:
            page.locator("button:has-text('Done')").first.click()
            print("Clicked Done")
            return True
        # try Next/Continue
        if page.locator("button:has-text('Next')").count() > 0:
            page.locator("button:has-text('Next')").first.click()
            continue
        if page.locator("button:has-text('Continue')").count() > 0:
            page.locator("button:has-text('Continue')").first.click()
            continue

        # fallback: look for buttons with aria-label 'Submit application'
        if page.locator("button[aria-label*='submit application' i]").count() > 0:
            page.locator("button[aria-label*='submit application' i]").first.click()
            return True

        # if no recognized control found, break
        break

    print("Could not finish easy apply for this job")
    # try to close modal
    try:
        if page.locator("button[aria-label='Dismiss']").count() > 0:
            page.locator("button[aria-label='Dismiss']").first.click()
    except:
        pass
    return False

def main():
    applied = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()
        login(page)
        links = search_job_links(page, max_links=50)
        for link in links:
            if applied >= MAX_APPLIES:
                print("Reached MAX_APPLIES", MAX_APPLIES)
                break
            try:
                ok = try_easy_apply(page, link)
                if ok:
                    applied += 1
                    print("Applied count:", applied)
                # polite random pause between applications
                human_pause(3.0, 5.0)
            except Exception as e:
                print("Error processing link:", e)
        print("Done. Applied:", applied)
        context.close()
        browser.close()

if __name__ == "__main__":
    main()
