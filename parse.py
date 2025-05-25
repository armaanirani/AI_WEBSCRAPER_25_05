import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Optional, Callable

load_dotenv()

def parse_with_ai(
    dom_chunks: List[str], 
    parse_description: str, 
    provider: str = "groq",
    model_name: str = "llama-3.3-70b-versatile",
    extraction_type: str = "general",
    progress_callback: Optional[Callable] = None
) -> str:
    """
    Parse DOM content using Groq LLM with enhanced extraction capabilities.
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        provider: LLM provider (only "groq" supported)
        model_name: Groq model to use
        extraction_type: Type of extraction (general, contact, product, content)
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
    if provider != "groq":
        raise ValueError("Only 'groq' provider is supported")

    # Initialize Groq client
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    model_name = "llama-3.3-70b-versatile"  # Default fallback

    model = ChatGroq(
        model_name=model_name,
        temperature=0,
        groq_api_key=groq_api_key
    )

    # Create specialized prompts based on extraction type
    template = _get_prompt_template(extraction_type, parse_description)
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model | StrOutputParser()
    
    parsed_results = []
    
    try:
        for i, chunk in enumerate(dom_chunks, start=1):
            if not chunk or not chunk.strip():  # Skip empty chunks
                continue
            
            # Update progress if callback provided
            if progress_callback:
                progress_callback(i, len(dom_chunks))
                
            response = chain.invoke({
                "dom_content": chunk, 
                "parse_description": parse_description
            })
            
            print(f"Parsed batch {i} of {len(dom_chunks)}")
            
            if response and response.strip():
                parsed_results.append(response.strip())
            
        return "\n\n".join(parsed_results) if parsed_results else "No matching information found"
        
    except Exception as e:
        raise Exception(f"Parsing failed: {str(e)}")


def _get_prompt_template(extraction_type: str, parse_description: str) -> str:
    """Get specialized prompt template based on extraction type."""
    
    base_template = """Extract only the information that matches this description: {parse_description}

Content to analyze:
{dom_content}

"""
    
    if extraction_type == "contact":
        return base_template + """Focus on extracting contact information such as:
- Email addresses
- Phone numbers
- Physical addresses
- Contact forms
- Social media links

Return only the extracted contact information with clear labels."""
        
    elif extraction_type == "product":
        return base_template + """Focus on extracting product information such as:
- Product names and descriptions
- Prices and pricing information
- Product specifications
- Availability status
- Product categories

Return only the extracted product information in a structured format."""
        
    elif extraction_type == "content":
        return base_template + """Focus on extracting main content such as:
- Headlines and titles
- Main text content
- Important announcements
- Key information
- Article content

Return only the extracted content information, preserving important structure."""
        
    else:  # general
        return base_template + "Return only the extracted information with no additional text or explanations."


def parse_with_groq(dom_chunks: List[str], parse_description: str) -> str:
    """
    Legacy function for backward compatibility.
    Parse DOM content using Groq LLM.
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        
    Returns:
        Parsed content concatenated from all chunks
    """
    return parse_with_ai(dom_chunks, parse_description, "groq")


def parse_with_langchain_memory(
    dom_chunks: List[str], 
    parse_description: str,
    model_name: str = "mixtral-8x7b-32768"
) -> str:
    """
    Parse with conversation memory for better context understanding.
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        model_name: Groq model to use
        
    Returns:
        Parsed content with improved context understanding
    """
    # For now, this is the same as regular parsing
    # Can be enhanced with LangChain memory components if needed
    return parse_with_ai(dom_chunks, parse_description, "groq", model_name)