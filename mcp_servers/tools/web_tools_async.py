# web_tools_async.py
import asyncio
import traceback
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from readability.readability import Document
import trafilatura
import random
from pathlib import Path

DIFFICULT_WEBSITES_PATH = Path(__file__).parent / "difficult_websites.txt"

def get_random_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 Chrome/113.0.5672.92 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 Version/16.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 Chrome/117.0.5938.132 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G998B) AppleWebKit/537.36 Chrome/92.0.4515.159 Mobile Safari/537.36 SamsungBrowser/15.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 Version/16.6 Mobile Safari/604.1"
    ]
    return {"User-Agent": random.choice(user_agents)}


def is_difficult_website(url: str) -> bool:
    if not DIFFICULT_WEBSITES_PATH.exists():
        return False
    try:
        with open(DIFFICULT_WEBSITES_PATH, "r", encoding="utf-8") as f:
            difficult_sites = [line.strip().lower() for line in f if line.strip()]
        return any(domain in url.lower() for domain in difficult_sites)
    except Exception as e:
        print(f"⚠️ Failed to read difficult_websites.txt: {e}")
        return False

# Improved function to handle Unicode characters safely
def safe_text_cleanup(text: str) -> str:
    """Safely clean text by removing problematic characters while preserving readability"""
    if not text:
        return ""
    
    try:
        # First try to normalize Unicode
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        
        # Replace common problematic characters
        replacements = {
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Horizontal ellipsis
            '\u00a0': ' ',  # Non-breaking space
            '\u200b': '',   # Zero-width space
            '\u200c': '',   # Zero-width non-joiner
            '\u200d': '',   # Zero-width joiner
            '\u2028': '\n', # Line separator
            '\u2029': '\n', # Paragraph separator
            '\u00ad': '',   # Soft hyphen
            '\u2060': '',   # Word joiner
            '\u2061': '',   # Function application
            '\u2062': '',   # Invisible times
            '\u2063': '',   # Invisible separator
            '\u2064': '',   # Invisible plus
            '\u2066': '',   # Left-to-right isolate
            '\u2067': '',   # Right-to-left isolate
            '\u2068': '',   # First strong isolate
            '\u2069': '',   # Pop directional isolate
            '\u206a': '',   # Inhibit symmetric swapping
            '\u206b': '',   # Activate symmetric swapping
            '\u206c': '',   # Inhibit arabic form shaping
            '\u206d': '',   # Activate arabic form shaping
            '\u206e': '',   # National digit shapes
            '\u206f': '',   # Nominal digit shapes
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove other control characters except newlines and tabs
        import re
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Final safety check: ensure UTF-8 encoding
        return text.encode('utf-8', errors='replace').decode('utf-8')
        
    except Exception as e:
        print(f"Warning: Text cleanup failed: {e}")
        # Fallback: try to encode/decode with errors='replace'
        try:
            return text.encode('utf-8', errors='replace').decode('utf-8')
        except:
            return "[encoding error]"

def choose_best_text(visible, main, trafilatura_):
    # Simple heuristic: prefer main if long, fallback otherwise
    scores = {
        "visible": len(visible.strip()),
        "main": len(main.strip()),
        "trafilatura": len(trafilatura_.strip())
    }
    best = max(scores, key=scores.get)
    return {
        "visible": visible,
        "main": main,
        "trafilatura": trafilatura_
    }[best], best

async def web_tool_playwright(url: str, max_total_wait: int = 15) -> dict:
    result = {"url": url}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            # Wait until the page body has significant content (i.e., text is non-trivial)
            try:
                await page.wait_for_function(
                    """() => {
                        const body = document.querySelector('body');
                        return body && (body.innerText || "").length > 1000;
                    }""",
                    timeout=15000
                )
            except Exception as e:
                print("⚠️ Generic wait failed:", e)

            # Optional light sleep for residual JS rendering
            await asyncio.sleep(5)

            try:
                await page.evaluate("""() => {
                    window.stop();
                    document.querySelectorAll('script').forEach(s => s.remove());
                }""")
            except Exception as e:
                print("⚠️ JS stop failed:", e)

            html = await page.content()
            visible_text = await page.inner_text("body")
            title = await page.title()
            await browser.close()

            # Run parsing in background to free browser early
            try:
                main_text = await asyncio.to_thread(lambda: BeautifulSoup(Document(html).summary(), "html.parser").get_text(separator="\n", strip=True))
            except Exception as e:
                print("⚠️ Readability failed:", e)
                main_text = ""

            try:
                trafilatura_text = await asyncio.to_thread(lambda: trafilatura.extract(html) or "")
            except Exception as e:
                print("⚠️ Trafilatura failed:", e)
                trafilatura_text = ""

            best_text, source = choose_best_text(visible_text, main_text, trafilatura_text)

            result.update({
                "title": title,
                "html": html,
                "text": visible_text,
                "main_text": main_text,
                "trafilatura_text": trafilatura_text,
                "best_text": safe_text_cleanup(best_text),
                "best_text_source": source
            })

    except PlaywrightTimeoutError:
        result.update({
            "title": "[timeout: goto]",
            "html": "",
            "text": "[timed out]",
            "main_text": "[no HTML extracted]",
            "trafilatura_text": "",
            "best_text": "[no text]",
            "best_text_source": "timeout"
        })

    except Exception as e:
        traceback.print_exc()
        result.update({
            "title": "[error]",
            "html": "",
            "text": f"[error: {e}]",
            "main_text": "[no HTML extracted]",
            "trafilatura_text": "",
            "best_text": "[no text]",
            "best_text_source": "error"
        })

    return result

import httpx

async def smart_web_extract(url: str, timeout: int = 5) -> dict:

    headers = get_random_headers()

    try:

        if is_difficult_website(url):
            print(f"Detected difficult site ({url}) → skipping fast scrape")
            return await web_tool_playwright(url)


        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            html = response.content.decode("utf-8", errors="replace")

        doc = Document(html)
        main_html = doc.summary()
        main_text = BeautifulSoup(main_html, "html.parser").get_text(separator="\n", strip=True)
        visible_text = BeautifulSoup(html, "html.parser").get_text(separator="\n", strip=True)
        trafilatura_text = trafilatura.extract(html)
        best_text, best_source = choose_best_text(visible_text, main_text, trafilatura_text)

        if len(best_text) >= 300:
            return {
                "url": url,
                "title": Document(html).short_title(),
                "html": html,
                "text": visible_text,
                "main_text": main_text,
                "trafilatura_text": trafilatura_text,
                "best_text": safe_text_cleanup(best_text),
                "best_text_source": best_source
            }

        print("Fast scrape too small, falling back...")

    except Exception as e:
        print("Fast scrape failed:", e)

    # Fallback
    return await web_tool_playwright(url)


if __name__ == "__main__":
    print("starting scrape subprocess...")
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python web_tool_playwright_async.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    print("🚀 Trying smart scrape first...")
    result = asyncio.run(smart_web_extract(url))
    print(json.dumps(result, ensure_ascii=False))