import streamlit as st
import asyncio
import concurrent.futures
import re
import time
import aiohttp

async def check_url_status(session, url, status_counts):
    start_time = time.time()
    try:
        async with session.head(url) as response:
            status = response.status
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts["Other"] += 1
    except aiohttp.ClientError:
        status_counts["Error"] += 1
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

        status_counts = {200: 0, 404: 0, 500: 0, "Other": 0, "Error": 0}

        if urls:
            concurrency = 50  # You can experiment with different values here

            async with aiohttp.ClientSession() as session:
                tasks = [check_url_status(session, url, status_counts) for url in urls]

                # Divide tasks into chunks to execute concurrently
                for chunk in [tasks[i:i+concurrency] for i in range(0, len(tasks), concurrency)]:
                    await asyncio.gather(*chunk)

        st.write(f"Total Links Checked: {len(urls)}")
        st.write(f"Status Code 200: {status_counts[200]}")
        st.write(f"Status Code 404: {status_counts[404]}")
        st.write(f"Status Code 500: {status_counts[500]}")
        st.write(f"Other Status Codes: {status_counts['Other']}")
        st.write(f"Errors: {status_counts['Error']}")

if __name__ == "__main__":
    asyncio.run(main())
