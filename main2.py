import streamlit as st
import asyncio
import concurrent.futures
import re
import time
import aiohttp

async def check_url_status(session, url, placeholder):
    start_time = time.time()
    try:
        async with session.head(url) as response:
            status = response.status
            placeholder.write(f"{url} - Status Code: {status}")
    except aiohttp.ClientError:
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

        total_time = 0
        if urls:
            concurrency = 50  # You can experiment with different values here

            async with aiohttp.ClientSession() as session:
                url_placeholders = [st.empty() for _ in range(len(urls))]
                tasks = [check_url_status(session, url, placeholder) for url, placeholder in zip(urls, url_placeholders)]

                # Divide tasks into chunks to execute concurrently
                for chunk in [tasks[i:i+concurrency] for i in range(0, len(tasks), concurrency)]:
                    times = await asyncio.gather(*chunk)
                    total_time += sum(times)

        st.write(f"Total Time Taken: {total_time:.2f} seconds")
        if urls:
            average_time_per_link = total_time / len(urls)
            st.write(f"Average Time Per Link: {average_time_per_link:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())