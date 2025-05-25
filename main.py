import streamlit as st
from scrape import scrape_website


st.title("AI Web Scraper")
url = st.text_input("Enter the URL to scrape:")

if st.button("Scrape Site"):
    st.write(f"Scraping the site: {url}")
    result = scrape_website(url)
    print(result)