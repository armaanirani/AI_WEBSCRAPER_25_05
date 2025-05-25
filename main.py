import streamlit as st
import os
from scrape import scrape_website, split_dom_content, clean_body_content, extract_body_content
from parse import parse_with_ai

# Page configuration
st.set_page_config(
    page_title="AI Web Scraper",
    page_icon="🕷️",
    layout="wide"
)

st.title("🕷️ AI Web Scraper")
st.markdown("Scrape websites and extract specific information using AI")

# Sidebar for API configuration
st.sidebar.header("🔑 API Configuration")
api_provider = st.sidebar.selectbox(
    "Choose AI Provider",
    ["OpenAI", "Groq"],
    help="Select your preferred AI API provider"
)

if api_provider == "OpenAI":
    api_key = st.sidebar.text_input(
        "OpenAI API Key", 
        type="password", 
        help="Enter your OpenAI API key",
        placeholder="sk-..."
    )
    model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
else:
    api_key = st.sidebar.text_input(
        "Groq API Key", 
        type="password", 
        help="Enter your Groq API key",
        placeholder="gsk_..."
    )
    model_options = ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]

selected_model = st.sidebar.selectbox("Select Model", model_options)

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
    elif not api_key:
        st.error(f"❌ Please enter your {api_provider} API key in the sidebar")
    else:
        with st.spinner("🔄 Scraping website..."):
            try:
                # Validate URL format
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                result = scrape_website(url)
                body_content = extract_body_content(result)
                cleaned_content = clean_body_content(body_content)
                
                if not cleaned_content.strip():
                    st.warning("⚠️ No content found on the website")
                else:
                    st.session_state.dom_content = cleaned_content
                    st.session_state.source_url = url
                    st.success(f"✅ Successfully scraped {len(cleaned_content)} characters from {url}")
                    
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
        elif not api_key:
            st.error(f"❌ Please enter your {api_provider} API key in the sidebar")
        else:
            with st.spinner("🤖 AI is analyzing the content..."):
                try:
                    # Set API key as environment variable
                    if api_provider == "OpenAI":
                        os.environ["OPENAI_API_KEY"] = api_key
                    else:
                        os.environ["GROQ_API_KEY"] = api_key
                    
                    dom_chunks = split_dom_content(st.session_state.dom_content)
                    st.info(f"📊 Processing {len(dom_chunks)} content chunks...")
                    
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    result = parse_with_ai(
                        dom_chunks, 
                        parse_description, 
                        api_provider.lower(),
                        selected_model,
                        progress_callback=lambda i, total: (
                            progress_bar.progress(i / total),
                            status_text.text(f"Processing chunk {i}/{total}...")
                        )
                    )
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Processing complete!")
                    
                    if result.strip():
                        st.success("🎉 Information extracted successfully!")
                        
                        # Display results in a nice format
                        st.subheader("📋 Extracted Information:")
                        st.markdown(result)
                        
                        # Download option
                        st.download_button(
                            label="💾 Download Results",
                            data=result,
                            file_name=f"extracted_info_{st.session_state.get('source_url', 'website').replace('https://', '').replace('http://', '').replace('/', '_')}.txt",
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
                    progress_bar.empty()
                    status_text.empty()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🚀 Enhanced AI Web Scraper | Built with Streamlit</p>
        <p><small>Supports OpenAI and Groq APIs for intelligent content extraction</small></p>
    </div>
    """,
    unsafe_allow_html=True
)