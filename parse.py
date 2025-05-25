import os
import time
from typing import List, Optional, Callable
import openai
from groq import Groq

class AIParser:
    """Enhanced AI parser supporting multiple providers."""
    
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.model = model
        
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        elif self.provider == "groq":
            self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def create_prompt(self, dom_content: str, parse_description: str) -> str:
        """Create an optimized prompt for content extraction."""
        return f"""You are an expert data extraction assistant. Your task is to extract specific information from web content.

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

    def parse_chunk(self, chunk: str, parse_description: str) -> str:
        """Parse a single chunk of content."""
        if not chunk.strip():
            return ""
        
        try:
            prompt = self.create_prompt(chunk, parse_description)
            
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a precise data extraction assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a precise data extraction assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            return f"Error processing chunk: {str(e)}"
    
    def parse_content(self, dom_chunks: List[str], parse_description: str, 
                     progress_callback: Optional[Callable] = None) -> str:
        """Parse multiple chunks with progress tracking."""
        if not dom_chunks or not isinstance(dom_chunks, list):
            raise ValueError("dom_chunks must be a non-empty list")
        if not parse_description or not isinstance(parse_description, str):
            raise ValueError("parse_description must be a non-empty string")

        parsed_results = []
        total_chunks = len(dom_chunks)
        
        for i, chunk in enumerate(dom_chunks, start=1):
            if progress_callback:
                progress_callback(i, total_chunks)
            
            if not chunk.strip():  # Skip empty chunks
                continue
            
            try:
                result = self.parse_chunk(chunk, parse_description)
                if result and result != "No matching information found":
                    parsed_results.append(result)
                
                # Rate limiting to avoid API limits
                if i < total_chunks:  # Don't sleep after the last chunk
                    time.sleep(0.5)  # Adjust based on API rate limits
                    
            except Exception as e:
                parsed_results.append(f"Error in chunk {i}: {str(e)}")
        
        # Combine and clean results
        if parsed_results:
            combined_results = "\n\n".join(parsed_results)
            return self._clean_and_deduplicate(combined_results)
        else:
            return "No matching information found in the provided content."
    
    def _clean_and_deduplicate(self, content: str) -> str:
        """Clean and deduplicate extracted content."""
        lines = content.split('\n')
        cleaned_lines = []
        seen_lines = set()
        
        for line in lines:
            line = line.strip()
            if line and line not in seen_lines and "Error" not in line:
                cleaned_lines.append(line)
                seen_lines.add(line)
        
        return '\n'.join(cleaned_lines)


def parse_with_ai(dom_chunks: List[str], parse_description: str, 
                  provider: str = "openai", model: str = "gpt-4o-mini",
                  progress_callback: Optional[Callable] = None) -> str:
    """
    Parse DOM content using AI models (OpenAI or Groq).
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        provider: AI provider ("openai" or "groq")
        model: Model name to use
        progress_callback: Optional callback for progress updates
        
    Returns:
        Parsed and cleaned content
        
    Raises:
        ValueError: If inputs are invalid
        Exception: For API or parsing errors
    """
    try:
        parser = AIParser(provider, model)
        return parser.parse_content(dom_chunks, parse_description, progress_callback)
    except Exception as e:
        raise Exception(f"AI parsing failed: {str(e)}")


# Utility function for backwards compatibility
def parse_with_ollama(dom_chunks: List[str], parse_description: str) -> str:
    """Backwards compatibility function - now uses OpenAI by default."""
    return parse_with_ai(dom_chunks, parse_description, "openai", "gpt-4o-mini")