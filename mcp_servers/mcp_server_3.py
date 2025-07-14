from mcp.server.fastmcp import FastMCP, Context
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import urllib.parse
import sys
import traceback
from datetime import datetime, timedelta
import time
import re
from pydantic import BaseModel, Field
from models import SearchInput, UrlInput, URLListOutput, SummaryInput
from models import PythonCodeOutput
from tools.web_tools_async import smart_web_extract
from tools.switch_search_method import smart_search
from mcp.types import TextContent
from google import genai
from dotenv import load_dotenv
import asyncio
import os
import random
import codecs

# Force UTF-8 encoding for the entire process
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Set default encoding for all file operations
import locale
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass  # Fallback to system default

# Configure stdout/stderr for UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def safe_str(obj) -> str:
    """Safely convert any object to string, handling Unicode characters"""
    try:
        if isinstance(obj, str):
            # Normalize Unicode and replace problematic characters
            import unicodedata
            text = unicodedata.normalize('NFKC', obj)
            
            # Replace problematic Unicode characters
            replacements = {
                '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
                '\u2013': '-', '\u2014': '--', '\u2026': '...',
                '\u00a0': ' ', '\u200b': '', '\u200c': '', '\u200d': ''
            }
            
            for old, new in replacements.items():
                text = text.replace(old, new)
            
            # Remove control characters except newlines and tabs
            import re
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
            
            # Final safety check: ensure UTF-8 encoding
            return text.encode('utf-8', errors='replace').decode('utf-8')
        return str(obj).encode('utf-8', errors='replace').decode('utf-8')
    except UnicodeEncodeError:
        try:
            return obj.encode('utf-8', errors='replace').decode('utf-8')
        except:
            return "[encoding error]"

def safe_json_serialize(obj) -> str:
    """Safely serialize object to JSON string with UTF-8 encoding"""
    try:
        import json
        
        # Deep clean the object before serialization
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {safe_str(k): clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, str):
                return safe_str(obj)
            else:
                return safe_str(obj)
        
        # Clean the object first
        cleaned_obj = clean_for_json(obj)
        
        # Use ensure_ascii=False to preserve Unicode characters
        json_str = json.dumps(cleaned_obj, ensure_ascii=False, default=str, separators=(',', ':'))
        
        # Ensure the JSON string can be encoded as UTF-8
        return json_str.encode('utf-8', errors='replace').decode('utf-8')
    except Exception as e:
        # Fallback: try to serialize with minimal data
        try:
            fallback_data = {
                "error": "serialization_failed",
                "message": safe_str(str(e)),
                "data_type": str(type(obj))
            }
            return json.dumps(fallback_data, ensure_ascii=False, default=str)
        except:
            return '{"error": "complete_serialization_failure"}'

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize FastMCP server
mcp = FastMCP("ddg-search", timeout=20)

@mcp.tool()
async def search_web_with_text_content(input: SearchInput, ctx: Context) -> dict:
    """Search web and return URLs with extracted text content. Gets both URLs and readable text from top search results."""
    
    try:
        # Step 1: Get URLs using existing function
        urls = await smart_search(input.query, input.max_results)
        
        # if not urls:
        #     # Fallback: provide basic information for common queries
        #     fallback_info = get_fallback_info(input.query)
        #     return {
        #         "content": [
        #             TextContent(
        #                 type="text",
        #                 text=fallback_info
        #             )
        #         ]
        #     }
        
        # Clean URLs to prevent encoding issues
        cleaned_urls = []
        for url in urls:
            try:
                cleaned_url = safe_str(url)
                if cleaned_url and cleaned_url.startswith('http'):
                    cleaned_urls.append(cleaned_url)
            except Exception as e:
                print(f"Warning: Failed to clean URL {url}: {e}")
                continue
        
        # if not cleaned_urls:
        #     # Fallback: provide basic information for common queries
        #     fallback_info = get_fallback_info(input.query)
        #     return {
        #         "content": [
        #             TextContent(
        #                 type="text",
        #                 text=fallback_info
        #             )
        #         ]
        #     }
        
        # Step 2: Extract text content from each URL
        results = []
        max_extracts = min(len(cleaned_urls), 5)  # Limit to avoid timeout
        
        for i, url in enumerate(cleaned_urls[:max_extracts]):
            try:
                # Use existing web extraction function
                web_result = await asyncio.wait_for(smart_web_extract(url), timeout=15)
                text_content = web_result.get("best_text", "")[:4000]  # Limit length
                
                # Enhanced text cleaning to prevent encoding issues
                try:
                    import unicodedata
                    # Normalize Unicode first
                    text_content = unicodedata.normalize('NFKC', text_content)
                    
                    # Replace problematic Unicode characters
                    replacements = {
                        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
                        '\u2013': '-', '\u2014': '--', '\u2026': '...',
                        '\u00a0': ' ', '\u200b': '', '\u200c': '', '\u200d': '',
                        '\u2028': '\n', '\u2029': '\n'  # Line separators
                    }
                    
                    for old, new in replacements.items():
                        text_content = text_content.replace(old, new)
                    
                    # Remove control characters except newlines and tabs
                    import re
                    text_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text_content)
                    
                    # Clean up whitespace
                    text_content = text_content.replace('\n', ' ').replace('  ', ' ').strip()
                    
                    # Final safety check
                    text_content = text_content.encode('utf-8', errors='replace').decode('utf-8')
                    
                except Exception as e:
                    print(f"Warning: Text cleaning failed for {url}: {e}")
                    # Fallback cleaning
                    text_content = text_content.replace('\n', ' ').replace('  ', ' ').strip()
                    text_content = text_content.encode('utf-8', errors='replace').decode('utf-8')
                
                # Create result with safe encoding
                result_item = {
                    "url": safe_str(url),
                    "content": text_content if text_content.strip() else "[error] No readable content found",
                    "rank": i + 1
                }
                
                # Add images if available (with safe encoding)
                if "images" in web_result:
                    try:
                        result_item["images"] = [safe_str(img) for img in web_result.get("images", [])]
                    except:
                        result_item["images"] = []
                
                results.append(result_item)
                
            except asyncio.TimeoutError:
                results.append({
                    "url": safe_str(url),
                    "content": "[error] Timeout while extracting content",
                    "rank": i + 1
                })
            except Exception as e:
                print(f"Error extracting content from {url}: {safe_str(e)}")
                results.append({
                    "url": safe_str(url),
                    "content": f"[error] {safe_str(e)}",
                    "rank": i + 1
                })
        
        # Add remaining URLs without content extraction
        for i, url in enumerate(cleaned_urls[max_extracts:], start=max_extracts):
            results.append({
                "url": safe_str(url),
                "content": "[not extracted] Content limit reached",
                "rank": i + 1
            })
        
        # Return structured results with safe encoding
        try:
            # Convert results to JSON string with UTF-8 encoding
            results_text = safe_json_serialize(results)
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=results_text
                    )
                ]
            }
        except Exception as e:
            print(f"Serialization error: {e}")
            # Fallback: return minimal error response
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"[error] Failed to serialize results: {safe_str(e)}"
                    )
                ]
            }
        
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        error_msg = safe_str(e)
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"[error] {error_msg}"
                )
            ]
        }


# def get_fallback_info(query: str) -> str:
#     """Provide basic fallback information for common queries when web search fails"""
#     query_lower = query.lower()
    
#     # President of India fallback
#     if "president" in query_lower and "india" in query_lower:
#         return safe_json_serialize([{
#             "url": "https://presidentofindia.gov.in/",
#             "content": "The President of India is the Head of State and the first citizen of India. The current President is Droupadi Murmu, who took office on July 25, 2022. She is the 15th President of India and the second woman to hold this office. The President serves as the Supreme Commander of the Indian Armed Forces and has various constitutional powers including the ability to appoint the Prime Minister and other constitutional functionaries.",
#             "rank": 1
#         }])
    
#     # General fallback
#     return safe_json_serialize([{
#         "url": "https://example.com",
#         "content": f"Unable to retrieve specific information for '{query}'. Please try rephrasing your query or check your internet connection.",
#         "rank": 1
#     }])


# Duckduck not responding? Check this: https://html.duckduckgo.com/html
@mcp.tool()
async def fetch_search_urls(input: SearchInput, ctx: Context) -> URLListOutput:
    """Get top website URLs for your search query. Just get's the URL's not the contents"""

    try:
        urls = await smart_search(input.query, input.max_results)
        return URLListOutput(result=urls)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        error_msg = safe_str(e)
        return URLListOutput(result=[f"[error] {error_msg}"])


@mcp.tool()
async def webpage_url_to_raw_text(url: str) -> dict:
    """Extract readable text from a webpage"""
    try:
        result = await asyncio.wait_for(smart_web_extract(url), timeout=25)
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"[{result.get('best_text_source', '')}] " + result.get("best_text", "")[:8000]
                )
            ]
        }
    except asyncio.TimeoutError:
        return {
            "content": [
                TextContent(
                    type="text",
                    text="[error] Timed out while extracting web content"
                )
            ]
        }
    except Exception as e:
        error_msg = safe_str(e)
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"[error] {error_msg}"
                )
            ]
        }


@mcp.tool()
async def webpage_url_to_llm_summary(input: SummaryInput, ctx: Context) -> dict:
    """Summarize the webpage using a custom prompt if provided, otherwise fallback to default."""
    try:
        result = await asyncio.wait_for(smart_web_extract(input.url), timeout=25)
        text = result.get("best_text", "")[:8000]

        if not text.strip():
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="[error] Empty or unreadable content from webpage."
                    )
                ]
            }

        # Improved text cleaning to handle Unicode characters
        try:
            import unicodedata
            clean_text = unicodedata.normalize('NFKC', text)
            
            # Replace problematic Unicode characters
            replacements = {
                '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
                '\u2013': '-', '\u2014': '--', '\u2026': '...',
                '\u00a0': ' ', '\u200b': '', '\u200c': '', '\u200d': ''
            }
            
            for old, new in replacements.items():
                clean_text = clean_text.replace(old, new)
            
            # Remove control characters except newlines and tabs
            import re
            clean_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', clean_text)
            clean_text = clean_text.strip()
            
        except Exception as e:
            print(f"Warning: Text cleaning failed: {e}")
            # Fallback to simple encoding
            clean_text = text.encode("utf-8", errors="replace").decode("utf-8").strip()

        prompt = input.prompt or (
            "Summarize this text as best as possible. Keep important entities and values intact. "
            "Only reply back in summary, and not extra description."
        )

        full_prompt = f"{prompt.strip()}\n\n[text below]\n{clean_text}"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )

        raw = response.candidates[0].content.parts[0].text
        
        # Clean the summary response as well
        try:
            summary = unicodedata.normalize('NFKC', raw)
            for old, new in replacements.items():
                summary = summary.replace(old, new)
            summary = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', summary)
            summary = summary.strip()
        except Exception as e:
            print(f"Warning: Summary cleaning failed: {e}")
            summary = raw.encode("utf-8", errors="replace").decode("utf-8").strip()

        return {
            "content": [
                TextContent(
                    type="text",
                    text=safe_str(summary)
                )
            ]
        }

    except asyncio.TimeoutError:
        return {
            "content": [
                TextContent(
                    type="text",
                    text="[error] Timed out while extracting web content."
                )
            ]
        }

    except Exception as e:
        error_msg = safe_str(e)
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"[error] {error_msg}"
                )
            ]
        }


def mcp_log(level: str, message: str) -> None:
    sys.stderr.write(f"{level}: {message}\n")
    sys.stderr.flush()


if __name__ == "__main__":
    # Set up global exception handler for encoding errors
    def handle_unicode_error(exctype, value, traceback_obj):
        if exctype == UnicodeEncodeError:
            print(f"Unicode encoding error caught: {value}", file=sys.stderr)
            return True
        return False
    
    sys.excepthook = handle_unicode_error
    
    print("mcp_server_3.py READY")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
            mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...")