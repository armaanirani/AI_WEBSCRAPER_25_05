import os
import time
from typing import List, Optional, Callable
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import BaseMessage

class AIParser:
    """Enhanced AI parser using LangChain for multiple providers."""
    
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.model = model
        
        # Initialize LangChain LLM based on provider
        if self.provider == "openai":
            self.llm = ChatOpenAI(
                model=model,
                temperature=0.1,
                max_tokens=1500,
                api_key=api_key or os.getenv("OPENAI_API_KEY")
            )
        elif self.provider == "groq":
            self.llm = ChatGroq(
                model=model,
                temperature=0.1,
                max_tokens=1500,
                groq_api_key=api_key or os.getenv("GROQ_API_KEY")
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Create the extraction chain
        self.chain = self._create_extraction_chain()
    
    def _create_extraction_chain(self):
        """Create a LangChain extraction chain."""
        # System message template
        system_template = """You are an expert data extraction assistant. Your task is to extract specific information from web content with high precision and accuracy.

Your responsibilities:
- Extract ONLY information that directly matches the user's request
- Present information in a clear, organized format
- Use bullet points or numbered lists when appropriate
- If no matching information is found, respond with "No matching information found"
- Do not include explanations, commentary, or additional context
- Focus on accuracy and relevance"""

        # Human message template
        human_template = """CONTENT TO ANALYZE:
{dom_content}

EXTRACTION REQUEST:
{parse_description}

Please extract the requested information following the guidelines above."""

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
        # Create and return the chain
        return prompt | self.llm | StrOutputParser()
    
    def parse_chunk(self, chunk: str, parse_description: str) -> str:
        """Parse a single chunk of content using LangChain."""
        if not chunk.strip():
            return ""
        
        try:
            # Use the LangChain chain to process the chunk
            result = self.chain.invoke({
                "dom_content": chunk,
                "parse_description": parse_description
            })
            return result.strip()
                
        except Exception as e:
            return f"Error processing chunk: {str(e)}"
    
    def parse_content_with_batch(self, dom_chunks: List[str], parse_description: str, 
                                progress_callback: Optional[Callable] = None) -> str:
        """Parse multiple chunks with batch processing and progress tracking."""
        if not dom_chunks or not isinstance(dom_chunks, list):
            raise ValueError("dom_chunks must be a non-empty list")
        if not parse_description or not isinstance(parse_description, str):
            raise ValueError("parse_description must be a non-empty string")

        parsed_results = []
        total_chunks = len(dom_chunks)
        
        # Process chunks in batches for better performance
        batch_size = 3
        for batch_start in range(0, total_chunks, batch_size):
            batch_end = min(batch_start + batch_size, total_chunks)
            batch_chunks = dom_chunks[batch_start:batch_end]
            
            # Process batch
            batch_results = []
            for i, chunk in enumerate(batch_chunks):
                chunk_index = batch_start + i + 1
                
                if progress_callback:
                    progress_callback(chunk_index, total_chunks)
                
                if not chunk.strip():  # Skip empty chunks
                    continue
                
                try:
                    result = self.parse_chunk(chunk, parse_description)
                    if result and result != "No matching information found":
                        batch_results.append(result)
                        
                except Exception as e:
                    batch_results.append(f"Error in chunk {chunk_index}: {str(e)}")
            
            parsed_results.extend(batch_results)
            
            # Rate limiting between batches
            if batch_end < total_chunks:
                time.sleep(1.0)  # Longer delay between batches
        
        # Combine and clean results
        if parsed_results:
            combined_results = "\n\n".join(parsed_results)
            return self._clean_and_deduplicate(combined_results)
        else:
            return "No matching information found in the provided content."
    
    def create_advanced_extraction_chain(self, extraction_type: str = "general"):
        """Create specialized extraction chains for different types of content."""
        
        if extraction_type == "contact":
            system_template = """You are a contact information extraction specialist. Extract contact details including:
- Email addresses
- Phone numbers
- Physical addresses
- Social media handles
- Contact forms or contact pages
- Business hours
- Names and titles of key personnel"""
            
        elif extraction_type == "product":
            system_template = """You are a product information extraction specialist. Extract:
- Product names and descriptions
- Prices and pricing information
- Product specifications
- Availability status
- SKUs or product codes
- Categories and brands
- Customer reviews or ratings"""
            
        elif extraction_type == "content":
            system_template = """You are a content extraction specialist. Extract:
- Main headings and subheadings
- Key paragraphs and content sections
- Lists and bullet points
- Important dates and events
- Links and references
- Author information"""
            
        else:
            system_template = """You are an expert data extraction assistant. Extract any relevant information based on the user's specific request with high precision and accuracy."""

        human_template = """CONTENT TO ANALYZE:
{dom_content}

EXTRACTION REQUEST:
{parse_description}

Please extract the requested information in a clear, organized format."""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
        return prompt | self.llm | StrOutputParser()
    
    def parse_with_retry(self, chunk: str, parse_description: str, max_retries: int = 3) -> str:
        """Parse chunk with retry logic for better reliability."""
        for attempt in range(max_retries):
            try:
                result = self.parse_chunk(chunk, parse_description)
                if result and "Error processing chunk" not in result:
                    return result
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"Failed after {max_retries} attempts: {str(e)}"
                time.sleep(2 ** attempt)  # Exponential backoff
                
        return "Failed to process chunk after multiple attempts"
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
                  progress_callback: Optional[Callable] = None,
                  extraction_type: str = "general") -> str:
    """
    Parse DOM content using AI models with LangChain (OpenAI or Groq).
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        provider: AI provider ("openai" or "groq")
        model: Model name to use
        progress_callback: Optional callback for progress updates
        extraction_type: Type of extraction ("general", "contact", "product", "content")
        
    Returns:
        Parsed and cleaned content
        
    Raises:
        ValueError: If inputs are invalid
        Exception: For API or parsing errors
    """
    try:
        parser = AIParser(provider, model)
        
        # Use specialized chain if extraction type is specified
        if extraction_type != "general":
            parser.chain = parser.create_advanced_extraction_chain(extraction_type)
        
        return parser.parse_content_with_batch(dom_chunks, parse_description, progress_callback)
    except Exception as e:
        raise Exception(f"AI parsing with LangChain failed: {str(e)}")


def parse_with_langchain_memory(dom_chunks: List[str], parse_description: str,
                               provider: str = "openai", model: str = "gpt-4o-mini") -> str:
    """
    Parse content with conversation memory for better context understanding.
    
    Args:
        dom_chunks: List of DOM content chunks
        parse_description: Description of what to parse
        provider: AI provider ("openai" or "groq")
        model: Model name to use
        
    Returns:
        Parsed content with improved context understanding
    """
    from langchain.memory import ConversationBufferWindowMemory
    from langchain.chains import ConversationChain
    
    try:
        parser = AIParser(provider, model)
        
        # Create memory for context
        memory = ConversationBufferWindowMemory(k=3)  # Remember last 3 interactions
        
        # Create conversation chain with memory
        conversation = ConversationChain(
            llm=parser.llm,
            memory=memory,
            verbose=False
        )
        
        # Process chunks with context
        all_results = []
        context = f"I need to extract the following information: {parse_description}"
        
        for i, chunk in enumerate(dom_chunks):
            if not chunk.strip():
                continue
                
            prompt = f"""
            Context: {context}
            
            Content chunk {i+1}:
            {chunk}
            
            Extract only the relevant information based on the context above.
            """
            
            try:
                result = conversation.predict(input=prompt)
                if result and "No matching information found" not in result:
                    all_results.append(result.strip())
            except Exception as e:
                all_results.append(f"Error in chunk {i+1}: {str(e)}")
        
        return "\n\n".join(all_results) if all_results else "No matching information found."
        
    except Exception as e:
        raise Exception(f"LangChain memory parsing failed: {str(e)}")


# Utility function for backwards compatibility
def parse_with_ollama(dom_chunks: List[str], parse_description: str) -> str:
    """Backwards compatibility function - now uses OpenAI by default."""
    return parse_with_ai(dom_chunks, parse_description, "openai", "gpt-4o-mini")