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
    progress_callback: Optional[Callable] = None
) -> str:
    """
    Parse DOM content using LangChain with Groq.
    
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

    # Initialize Groq client through LangChain
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    model = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=groq_api_key
    )
    
    # Create prompt template
    template = """Extract only the information that matches this description: {parse_description}

Content to analyze:
{dom_content}

Return only the extracted information with no additional text or explanations."""
    
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
            
            # Process chunk with LangChain
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