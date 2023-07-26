import streamlit as st
import httpx
import asyncio
import concurrent.futures
import re
import time

async def check_url_status(url, placeholder):
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=10)
            status = response.status_code
            placeholder.write(f"{url} - Status Code: {status}")
    except httpx.RequestError:
        placeholder.write(f"{url} - Error")
    end_time = time.time()
    return end_time - start_time

def contains_url(line):
    # Regular expression to check if a line contains a URL
    url_pattern = r'https?://\S+'
    return re.search(url_pattern, line)

async def main():
    st.title("URL Checker Dashboard")
    url_input = st.text_area("Enter URLs (one per line)")
    lines = url_input.strip().split('\n')
    
    if st.button("Check URLs"):
        st.write("Checking URLs...")
        urls = [line.strip() for line in lines if contains_url(line)]

        url_placeholders = [st.empty() for _ in range(len(urls))]
        url_tasks = [check_url_status(url, placeholder) for url, placeholder in zip(urls, url_placeholders)]
        times = await asyncio.gather(*url_tasks)

        total_time = sum(times)
        average_time_per_link = total_time / len(urls) if len(urls) > 0 else 0

        st.write(f"Total Time Taken: {total_time:.2f} seconds")
        st.write(f"Average Time Per Link: {average_time_per_link:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())