from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string ('')."
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
)

model = OllamaLLM(model="deepseek-r1:14b")

def parse_with_ollama(dom_chunks, parse_description):
    """Parse DOM content using Ollama LLM based on description.
    
    Args:
        dom_chunks (list): List of DOM content chunks
        parse_description (str): Description of what to parse
        
    Returns:
        str: Parsed content concatenated from all chunks
        
    Raises:
        ValueError: If inputs are invalid
        Exception: For parsing errors
    """
    if not dom_chunks or not isinstance(dom_chunks, list):
        raise ValueError("dom_chunks must be a non-empty list")
    if not parse_description or not isinstance(parse_description, str):
        raise ValueError("parse_description must be a non-empty string")

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    
    parsed_results = []
    
    try:
        for i, chunk in enumerate(dom_chunks, start=1):
            if not chunk:  # Skip empty chunks
                continue
                
            response = chain.invoke({
                "dom_content": chunk, 
                "parse_description": parse_description
            })
            print(f"Parsed batch {i} of {len(dom_chunks)}")
            parsed_results.append(str(response))
            
        return "\n".join(parsed_results) if parsed_results else ""
    except Exception as e:
        raise Exception(f"Parsing failed: {str(e)}")
