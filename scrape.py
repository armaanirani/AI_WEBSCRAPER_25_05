import os
import time
import requests
from urllib.parse import urlparse
from typing import List
import selenium.webdriver as webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_website(url: str, timeout: int = 30) -> str:
    """
    Scrape website with fallback mechanism.
    
    Args:
        url: Website URL to scrape
        timeout: Request timeout in seconds
        
    Returns:
        HTML content of the website
        
    Raises:
        Exception: If both scraping methods fail
    """
    # Validate URL
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Validate URL format
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError("Invalid URL format")
    
    # Try requests first (faster)
    try:
        return _scrape_with_requests(url, timeout)
    except Exception as requests_error:
        logger.warning(f"Requests failed: {requests_error}")
        logger.info("Falling back to Selenium method...")
        try:
            return _scrape_with_selenium(url, timeout)
        except Exception as selenium_error:
            raise Exception(f"Both scraping methods failed. Requests: {requests_error}. Selenium: {selenium_error}")


def _scrape_with_requests(url: str, timeout: int) -> str:
    """Scrape using requests (faster for static content)."""
    logger.info(f"Starting requests scraping for: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    logger.info("Successfully scraped with requests")
    return response.text


def _scrape_with_selenium(url: str, timeout: int) -> str:
    """Scrape website using Selenium."""
    logger.info(f"Starting Selenium scraping for: {url}")
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    try:
        # Try to create driver without specifying path first
        try:
            driver = webdriver.Chrome(options=options)
        except Exception:
            # Try with common paths
            possible_paths = [
                "chromedriver.exe",
                "chromedriver",
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    service = Service(path)
                    driver = webdriver.Chrome(service=service, options=options)
                    break
            
            if not driver:
                raise Exception("ChromeDriver not found. Please install ChromeDriver.")
        
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(2)  # Wait for dynamic content
        
        html = driver.page_source
        logger.info("Successfully scraped with Selenium")
        return html
        
    except TimeoutException:
        raise Exception(f"Page load timeout after {timeout} seconds")
    except Exception as e:
        raise Exception(f"Selenium scraping failed: {str(e)}")
    finally:
        if driver:
            driver.quit()


def extract_body_content(html_content: str) -> str:
    """
    Extract body content from HTML.
    
    Args:
        html_content: Raw HTML content
        
    Returns:
        Body content as string
    """
    if not html_content:
        return ""
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        body_content = soup.body
        if body_content:
            return str(body_content)
        else:
            return str(soup)
    except Exception as e:
        logger.warning(f"Error extracting body content: {e}")
        return html_content


def clean_body_content(body_content: str) -> str:
    """
    Clean and normalize body content.
    
    Args:
        body_content: Raw body content
        
    Returns:
        Cleaned text content
    """
    if not body_content:
        return ""
    
    try:
        soup = BeautifulSoup(body_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                           'aside', 'noscript', 'iframe', 'form']):
            element.extract()
        
        # Remove comments
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Get text with better formatting
        text = soup.get_text(separator="\n", strip=True)
        
        # Clean up the text
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and len(line) > 2:
                lines.append(line)
        
        # Remove consecutive duplicates
        cleaned_lines = []
        prev_line = ""
        for line in lines:
            if line != prev_line:
                cleaned_lines.append(line)
                prev_line = line
        
        return "\n".join(cleaned_lines)
        
    except Exception as e:
        logger.warning(f"Error cleaning content: {e}")
        soup = BeautifulSoup(body_content, 'html.parser')
        return soup.get_text()


def split_dom_content(dom_content: str, max_length: int = 6000) -> List[str]:
    """
    Split DOM content into manageable chunks.
    
    Args:
        dom_content: Text content to split
        max_length: Maximum length per chunk
        
    Returns:
        List of content chunks
    """
    if not dom_content:
        return []
    
    if len(dom_content) <= max_length:
        return [dom_content]
    
    chunks = []
    start = 0
    
    while start < len(dom_content):
        end = start + max_length
        
        if end >= len(dom_content):
            chunks.append(dom_content[start:])
            break
        
        # Try to break at a good point
        chunk = dom_content[start:end]
        
        for break_char in ['\n\n', '. ', '.\n', '\n']:
            break_pos = chunk.rfind(break_char)
            if break_pos > max_length * 0.7:
                chunk = dom_content[start:start + break_pos + len(break_char)]
                break
        
        chunks.append(chunk.strip())
        start += len(chunk)
    
    return [chunk for chunk in chunks if chunk.strip()]