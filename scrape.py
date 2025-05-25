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
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """Enhanced web scraper with better reliability and error handling."""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with optimal configuration."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Enhanced Chrome options for better reliability
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Faster loading
        options.add_argument("--disable-javascript")  # For basic scraping
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Try different possible ChromeDriver paths
        possible_paths = [
            "chromedriver.exe",
            "chromedriver",
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            os.path.expanduser("~/chromedriver")
        ]
        
        chrome_driver_path = None
        for path in possible_paths:
            if os.path.exists(path):
                chrome_driver_path = path
                break
        
        if not chrome_driver_path:
            # Try without specifying path (assume it's in PATH)
            try:
                return webdriver.Chrome(options=options)
            except Exception:
                raise Exception("ChromeDriver not found. Please install ChromeDriver and ensure it's in your PATH or current directory.")
        
        try:
            service = Service(chrome_driver_path)
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            raise Exception(f"Failed to initialize ChromeDriver: {str(e)}")
    
    def scrape_with_selenium(self, url: str) -> str:
        """Scrape website using Selenium."""
        logger.info(f"Starting Selenium scraping for: {url}")
        
        try:
            self.driver = self._setup_driver()
            self.driver.set_page_load_timeout(self.timeout)
            
            # Navigate to the URL
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            html = self.driver.page_source
            logger.info("Successfully scraped with Selenium")
            return html
            
        except TimeoutException:
            raise Exception(f"Page load timeout after {self.timeout} seconds")
        except WebDriverException as e:
            raise Exception(f"WebDriver error: {str(e)}")
        except Exception as e:
            raise Exception(f"Selenium scraping failed: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def scrape_with_requests(self, url: str) -> str:
        """Fallback scraping using requests (faster for static content)."""
        logger.info(f"Starting requests scraping for: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info("Successfully scraped with requests")
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"Requests scraping failed: {str(e)}")


def scrape_website(url: str, use_selenium: bool = True, timeout: int = 30) -> str:
    """
    Scrape website with fallback mechanism.
    
    Args:
        url: Website URL to scrape
        use_selenium: Whether to try Selenium first (default: True)
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
    
    scraper = WebScraper(headless=True, timeout=timeout)
    
    if use_selenium:
        try:
            return scraper.scrape_with_selenium(url)
        except Exception as selenium_error:
            logger.warning(f"Selenium failed: {selenium_error}")
            logger.info("Falling back to requests method...")
            try:
                return scraper.scrape_with_requests(url)
            except Exception as requests_error:
                raise Exception(f"Both scraping methods failed. Selenium: {selenium_error}. Requests: {requests_error}")
    else:
        try:
            return scraper.scrape_with_requests(url)
        except Exception as requests_error:
            logger.warning(f"Requests failed: {requests_error}")
            logger.info("Falling back to Selenium method...")
            try:
                return scraper.scrape_with_selenium(url)
            except Exception as selenium_error:
                raise Exception(f"Both scraping methods failed. Requests: {requests_error}. Selenium: {selenium_error}")


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
            # If no body tag, return the entire content
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
            if line and len(line) > 2:  # Filter out very short lines
                lines.append(line)
        
        # Remove excessive whitespace and duplicates
        cleaned_lines = []
        prev_line = ""
        for line in lines:
            if line != prev_line:  # Remove consecutive duplicates
                cleaned_lines.append(line)
                prev_line = line
        
        return "\n".join(cleaned_lines)
        
    except Exception as e:
        logger.warning(f"Error cleaning content: {e}")
        # Fallback to simple text extraction
        soup = BeautifulSoup(body_content, 'html.parser')
        return soup.get_text()


def split_dom_content(dom_content: str, max_length: int = 6000, overlap: int = 200) -> List[str]:
    """
    Split DOM content into manageable chunks with overlap.
    
    Args:
        dom_content: Text content to split
        max_length: Maximum length per chunk
        overlap: Number of characters to overlap between chunks
        
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
            # Last chunk
            chunks.append(dom_content[start:])
            break
        
        # Try to break at a sentence or paragraph boundary
        chunk = dom_content[start:end]
        
        # Look for good breaking points
        for break_char in ['\n\n', '. ', '.\n', '\n']:
            break_pos = chunk.rfind(break_char)
            if break_pos > max_length * 0.7:  # Don't break too early
                chunk = dom_content[start:start + break_pos + len(break_char)]
                break
        
        chunks.append(chunk.strip())
        start += len(chunk) - overlap
    
    return [chunk for chunk in chunks if chunk.strip()]


# Utility functions for additional functionality
def get_page_title(html_content: str) -> str:
    """Extract page title from HTML."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else "No Title"
    except:
        return "No Title"


def get_meta_description(html_content: str) -> str:
    """Extract meta description from HTML."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '').strip() if meta_desc else ""
    except:
        return ""