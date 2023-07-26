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
                status_counts[status]["count"] += 1
                status_counts[status]["urls"].append(url)
            else:
                status_counts[status] = {"count": 1, "urls": [url]}
    except aiohttp.ClientError:
        if "Error" in status_counts:
            status_counts["Error"]["count"] += 1
            status_counts["Error"]["urls"].append(url)
        else:
            status_counts["Error"] = {"count": 1, "urls": [url]}
    end_time = time.time()
    return end_time - start_time

def contains_url(line):
    # Regular expression to check if a line contains a URL
    url_pattern = r'https?://\S+'
    return re.search(url_pattern, line)

async def main():
    st.title("URL Checker Dashboard")

    # Input parameters
    url_input = st.text_area("Enter URLs (one per line)")
    concurrency = st.number_input("Concurrency", value=50, step=10, min_value=1)
    urls_per_group = st.number_input("URLs per Group", value=100, step=10, min_value=1)

    lines = url_input.strip().split('\n')
    
    if st.button("Check URLs"):
        st.write("Checking URLs...")
        urls = [line.strip() for line in lines if contains_url(line)]

        status_counts = {}

        if urls:
            async with aiohttp.ClientSession() as session:
                tasks = [check_url_status(session, url, status_counts) for url in urls]

                # Divide tasks into chunks to execute concurrently
                for chunk in [tasks[i:i+concurrency] for i in range(0, len(tasks), concurrency)]:
                    await asyncio.gather(*chunk)

        st.write(f"Total Links Checked: {len(urls)}")
        for status, info in status_counts.items():
            count = info["count"]
            st.write(f"Status Code {status}: {count}")
            urls_to_display = info["urls"]
            num_expanders = (len(urls_to_display) // urls_per_group) + 1

            for i in range(num_expanders):
                start_idx = i * urls_per_group
                end_idx = (i + 1) * urls_per_group
                with st.expander(f"View URLs {start_idx + 1} to {min(end_idx, len(urls_to_display))}"):
                    for url in urls_to_display[start_idx:end_idx]:
                        st.write(url)

        if "Error" in status_counts:
            st.write(f"Errors: {status_counts['Error']['count']}")
            with st.expander("View URLs with Errors"):
                for url in status_counts['Error']['urls']:
                    st.write(url)

if __name__ == "__main__":
    asyncio.run(main())