import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Optional, Callable

load_dotenv()

def parse_with_ai(
    dom_chunks: List[str], 
    parse_description: str,
    progress_callback: Optional[Callable] = None
) -> str:
    """
    Parse DOM content using OpenAI GPT.
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        progress_callback: Optional callback for progress updates
        
    Returns:
        Parsed content concatenated from all chunks
        
    Raises:
        ValueError: If inputs are invalid
        Exception: For parsing errors
    """
    if not dom_chunks or not isinstance(dom_chunks, list):
        raise ValueError("dom_chunks must be a non-empty list")
    if not parse_description or not isinstance(parse_description, str):
        raise ValueError("parse_description must be a non-empty string")

    # Initialize OpenAI client
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    client = OpenAI(api_key=openai_api_key)
    
    # Create prompt template
    template = f"""Extract only the information that matches this description: {parse_description}

Content to analyze:
{{content}}

Return only the extracted information with no additional text or explanations."""
    
    parsed_results = []
    
    try:
        for i, chunk in enumerate(dom_chunks, start=1):
            if not chunk or not chunk.strip():  # Skip empty chunks
                continue
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(i, len(dom_chunks))
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": template.format(content=chunk)}
                ],
                temperature=0,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            
            print(f"Parsed batch {i} of {len(dom_chunks)}")
            
            if result and result.strip():
                parsed_results.append(result.strip())
            
        return "\n\n".join(parsed_results) if parsed_results else "No matching information found"
        
    except Exception as e:
        raise Exception(f"Parsing failed: {str(e)}")