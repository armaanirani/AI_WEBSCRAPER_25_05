import streamlit as st
from scrape import scrape_website, split_dom_content, clean_body_content, extract_body_content


st.title("AI Web Scraper")
url = st.text_input("Enter the URL to scrape:")

if st.button("Scrape Site"):
    st.write(f"Scraping the site: {url}")
    try:
        result = scrape_website(url)
        body_content = extract_body_content(result)
        cleaned_content = clean_body_content(body_content)
        
        st.session_state.dom_content = cleaned_content
        
        with st.expander("View DOM Content"):
            st.text_area("DOM Content", value=cleaned_content, height=300)
    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")


if "dom_content" in st.session_state:
    parse_description = st.text_area("Describe what you want to parse?")
    
    if st.button("Parse DOM Content"):
        if parse_description:
            st.write("Parsing the content")
            
            dom_chunks = split_dom_content(st.session_state.dom_content)