import streamlit as st
import os
from scrape import scrape_website, split_dom_content, clean_body_content, extract_body_content
from parse import parse_with_ai, parse_with_langchain_memory

# Page configuration
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕷️",
    layout="wide"
)

st.title("🕷️ AI Web Scraper")
st.markdown("Scrape websites and extract specific information using AI")

# Fixed model - no sidebar selection needed
SELECTED_MODEL = "llama-3.3-70b-versatile"

# LangChain specific options
st.sidebar.header("🔗 Extraction Options")
extraction_type = st.sidebar.selectbox(
    "Extraction Type",
    ["general", "contact", "product", "content"],
    help="Choose specialized extraction type for better results"
)

use_memory = st.sidebar.checkbox(
    "Use Enhanced Processing",
    value=False,
    help="Enable enhanced processing for better context understanding"
)

# Scraping options
st.sidebar.markdown("---")
st.sidebar.header("🌐 Scraping Options")
use_selenium = st.sidebar.checkbox(
    "Use Selenium (Dynamic Content)",
    value=True,
    help="Enable for websites with JavaScript content"
)

timeout_seconds = st.sidebar.slider(
    "Timeout (seconds)",
    min_value=10,
    max_value=60,
    value=30,
    help="Maximum time to wait for page loading"
)

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input(
        "🌐 Enter Website URL", 
        placeholder="https://example.com",
        help="Enter the URL of the website you want to scrape"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    scrape_button = st.button("🚀 Scrape Website", type="primary", use_container_width=True)

# Scraping section
if scrape_button:
    if not url:
        st.error("❌ Please enter a URL")
    else:
        with st.spinner("🔄 Scraping website..."):
            try:
                # Validate URL format
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                result = scrape_website(url, use_selenium=use_selenium, timeout=timeout_seconds)
                body_content = extract_body_content(result)
                cleaned_content = clean_body_content(body_content)
                
                if not cleaned_content.strip():
                    st.warning("⚠️ No content found on the website")
                else:
                    st.session_state.dom_content = cleaned_content
                    st.session_state.source_url = url
                    st.success(f"✅ Successfully scraped {len(cleaned_content):,} characters from {url}")
                    
                    # Show content preview
                    with st.expander("👀 View Scraped Content Preview"):
                        preview = cleaned_content[:2000] + "..." if len(cleaned_content) > 2000 else cleaned_content
                        st.text_area("Content Preview", value=preview, height=300, disabled=True)
                        st.info(f"Total content length: {len(cleaned_content):,} characters")
                        
            except Exception as e:
                st.error(f"❌ Scraping failed: {str(e)}")
                st.info("💡 Make sure the URL is accessible and try again")

# Parsing section
if "dom_content" in st.session_state:
    st.markdown("---")
    st.header("🎯 Extract Information")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        parse_description = st.text_area(
            "📝 What information do you want to extract?",
            placeholder="e.g., Extract all email addresses, phone numbers, and contact information",
            height=100,
            help="Be specific about what you want to extract from the scraped content"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        parse_button = st.button("🔍 Extract Information", type="secondary", use_container_width=True)
    
    if parse_button:
        if not parse_description.strip():
            st.error("❌ Please describe what you want to extract")
        else:
            with st.spinner("🤖 AI is analyzing the content..."):
                try:
                    # Check for GROQ_API_KEY
                    if not os.getenv("GROQ_API_KEY"):
                        st.error("❌ GROQ_API_KEY not found in environment variables")
                        st.info("💡 Please set your GROQ_API_KEY in the environment variables")
                    else:
                        dom_chunks = split_dom_content(st.session_state.dom_content)
                        st.info(f"📊 Processing {len(dom_chunks)} content chunks with {SELECTED_MODEL}...")
                        
                        # Create progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Process chunks with Groq
                        if use_memory:
                            result = parse_with_langchain_memory(
                                dom_chunks, 
                                parse_description,
                                SELECTED_MODEL
                            )
                        else:
                            result = parse_with_ai(
                                dom_chunks, 
                                parse_description, 
                                "groq",
                                SELECTED_MODEL,
                                extraction_type=extraction_type,
                                progress_callback=lambda i, total: (
                                    progress_bar.progress(i / total),
                                    status_text.text(f"Processing chunk {i}/{total}...")
                                )
                            )
                        
                        progress_bar.progress(1.0)
                        status_text.text("✅ Processing complete!")
                        
                        if result and result.strip() and result != "No matching information found":
                            st.success("🎉 Information extracted successfully!")
                            
                            # Display results in a nice format
                            st.subheader("📋 Extracted Information:")
                            st.markdown(result)
                            
                            # Download option
                            filename = f"extracted_info_{st.session_state.get('source_url', 'website').replace('https://', '').replace('http://', '').replace('/', '_')}.txt"
                            st.download_button(
                                label="💾 Download Results",
                                data=result,
                                file_name=filename,
                                mime="text/plain"
                            )
                        else:
                            st.warning("⚠️ No matching information found based on your description")
                            st.info("💡 Try rephrasing your extraction request or check if the content contains what you're looking for")
                            
                except Exception as e:
                    st.error(f"❌ Extraction failed: {str(e)}")
                    st.info("💡 Please check your API key and try again")
                finally:
                    # Clean up progress indicators
                    try:
                        progress_bar.empty()
                        status_text.empty()
                    except:
                        pass

# Additional information section
if "dom_content" in st.session_state:
    st.markdown("---")
    st.header("📊 Content Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        word_count = len(st.session_state.dom_content.split())
        st.metric("Word Count", f"{word_count:,}")
    
    with col2:
        char_count = len(st.session_state.dom_content)
        st.metric("Character Count", f"{char_count:,}")
    
    with col3:
        chunk_count = len(split_dom_content(st.session_state.dom_content))
        st.metric("Processing Chunks", chunk_count)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🚀 AI Web Scraper | Built with Streamlit & Groq</p>
        <p><small>Powered by Groq LLMs for intelligent content extraction</small></p>
    </div>
    """,
    unsafe_allow_html=True
)