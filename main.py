import streamlit as st


st.title("AI Web Scraper")
url = st.text_input("Enter the URL to scrape:")

if st.button("Scrape Site"):
    st.write(f"Scraping the site: {url}")