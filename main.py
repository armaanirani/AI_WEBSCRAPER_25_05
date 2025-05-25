import streamlit as st
from scrape import scrape_website


st.title("AI Web Scraper")
url = st.text_input("Enter the URL to scrape:")

if st.button("Scrape Site"):
    st.write(f"Scraping the site: {url}")
    try:
        result = scrape_website(url)
        st.write("Scraping successful! Here's the page content:")
        st.code(result[:1000])  # Show first 1000 chars to avoid overwhelming UI
    except Exception as e:
        st.error(f"Scraping failed: {str(e)}")
