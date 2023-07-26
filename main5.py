import streamlit as st
import asyncio
import concurrent.futures
import re
import time
import aiohttp
import pandas as pd
from urllib.parse import urlparse
from st_aggrid import AgGrid
import os

async def check_url_status(session, url, status_counts, results_df):
    start_time = time.time()
    try:
        async with session.head(url) as response:
            status = response.status
            if status in status_counts:
                status_counts[status]["count"] += 1
                status_counts[status]["urls"].append(url)
            else:
                status_counts[status] = {"count": 1, "urls": [url]}

            # Extract main domain from the URL
            parsed_url = urlparse(url)
            main_domain = parsed_url.netloc
            true_domain = get_true_domain(main_domain)
            results_df = results_df.append({"url": url, "status_code": status, "main_domain": main_domain, "true_domain": true_domain}, ignore_index=True)
    except aiohttp.ClientError:
        if "Error" in status_counts:
            status_counts["Error"]["count"] += 1
            status_counts["Error"]["urls"].append(url)
        else:
            status_counts["Error"] = {"count": 1, "urls": [url]}
        results_df = results_df.append({"url": url, "status_code": "Error", "main_domain": "", "true_domain": ""}, ignore_index=True)
    end_time = time.time()
    return end_time - start_time, results_df

def contains_url(line):
    # Regular expression to check if a line contains a URL
    url_pattern = r'https?://\S+'
    return re.search(url_pattern, line)

def get_true_domain(main_domain):
    # Extract the true domain based on the provided logic
    if main_domain.count('.') >= 2:
        true_domain = main_domain.split('.', 1)[1]
    else:
        true_domain = main_domain
    return true_domain

async def main():
    st.title("URL Checker Dashboard")

    # Input parameters
    url_input = st.text_area("Enter URLs (one per line)")
    concurrency = st.number_input("Concurrency", value=50, step=10, min_value=1)

    lines = url_input.strip().split('\n')

    results_df = pd.DataFrame(columns=["url", "status_code", "main_domain", "true_domain"])
    status_counts = {}

    if st.button("Check URLs"):
        st.write("Checking URLs...")
        files_to_remove = ['summary.pkl', 'detail.pkl']
        for file_name in files_to_remove:
            if os.path.exists(file_name):
                os.remove(file_name)
                print(f"File '{file_name}' has been removed.")
            else:
                print(f"File '{file_name}' does not exist.")
        urls = [line.strip() for line in lines if contains_url(line)]

        if urls:
            async with aiohttp.ClientSession() as session:
                tasks = [check_url_status(session, url, status_counts, results_df) for url in urls]

                # Divide tasks into chunks to execute concurrently
                for chunk in [tasks[i:i+concurrency] for i in range(0, len(tasks), concurrency)]:
                    results = await asyncio.gather(*chunk)

                    # Collect results and update the DataFrame
                    for elapsed_time, df in results:
                        results_df = results_df.append(df)

        st.write(f"Total Links Checked: {len(urls)}")
        for status, info in status_counts.items():
            count = info["count"]
            st.write(f"Status Code {status}: {count}")

        if "Error" in status_counts:
            st.write(f"Errors: {status_counts['Error']['count']}")

        if not results_df.empty:
            st.write("Results DataFrame (Grouped by true_domain and status_code):")
            grouped_df = results_df.groupby(['true_domain', 'status_code']).size().reset_index(name='count')
            grouped_df.to_pickle('summary.pkl')


            st.write("Original Results DataFrame:")
            results_df.to_pickle('detail.pkl')


if __name__ == "__main__":
    # files_to_remove = ['summary.pkl', 'detail.pkl']
    # for file_name in files_to_remove:
    #     if os.path.exists(file_name):
    #         os.remove(file_name)
    #         print(f"File '{file_name}' has been removed.")
    #     else:
    #         print(f"File '{file_name}' does not exist.")
    asyncio.run(main())
    try:
        dfSummary=pd.read_pickle('summary.pkl')
        AgGrid(data=dfSummary,key='summary')
        dfDetail=pd.read_pickle('detail.pkl')
        AgGrid(data=dfDetail,key='detail')
    except:
        st.error('No result')