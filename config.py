"""Configuration settings for the AI Web Scraper."""

import os
from typing import Dict, Any

# API Configuration
OPENAI_MODELS = [
    "gpt-4.1-nano-2025-04-14",
    "gpt-4.1-mini-2025-04-14", 
    "gpt-4o-mini-2024-07-18"
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant", 
    "gemma2-9b-it"
]

# Scraping Configuration
SCRAPING_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "chunk_size": 6000,
    "chunk_overlap": 200,
    "rate_limit_delay": 0.5,  # seconds between API calls
}

# Chrome Driver Configuration
CHROME_OPTIONS = [
    "--no-sandbox",
    "--disable-dev-shm-usage", 
    "--disable-gpu",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
]

# HTML Elements to Remove During Cleaning
ELEMENTS_TO_REMOVE = [
    'script', 'style', 'nav', 'header', 'footer',
    'aside', 'noscript', 'iframe', 'form', 'button'
]

# Default Prompts
DEFAULT_EXTRACTION_PROMPT = """You are an expert data extraction assistant. Your task is to extract specific information from web content.

CONTENT TO ANALYZE:
{dom_content}

EXTRACTION REQUEST:
{parse_description}

INSTRUCTIONS:
1. Extract ONLY the information that directly matches the request
2. Present the information in a clear, organized format
3. If you find multiple instances, list them clearly
4. If no matching information is found, respond with "No matching information found"
5. Do not include explanations or commentary, only the requested data
6. Use bullet points or numbered lists when appropriate for clarity

EXTRACTED INFORMATION:"""

# Error Messages
ERROR_MESSAGES = {
    "no_url": "❌ Please enter a URL",
    "no_api_key": "❌ Please enter your {} API key in the sidebar", 
    "no_description": "❌ Please describe what you want to extract",
    "scraping_failed": "❌ Scraping failed: {}",
    "parsing_failed": "❌ Extraction failed: {}",
    "invalid_url": "❌ Invalid URL format",
    "timeout": "❌ Request timed out. Please try again.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "scraping_success": "✅ Successfully scraped {:,} characters from {}",
    "parsing_success": "🎉 Information extracted successfully!",
}

def get_config() -> Dict[str, Any]:
    """Get application configuration."""
    return {
        "openai_models": OPENAI_MODELS,
        "groq_models": GROQ_MODELS,
        "scraping": SCRAPING_CONFIG,
        "chrome_options": CHROME_OPTIONS,
        "elements_to_remove": ELEMENTS_TO_REMOVE,
        "default_prompt": DEFAULT_EXTRACTION_PROMPT,
        "error_messages": ERROR_MESSAGES,
        "success_messages": SUCCESS_MESSAGES,
    }