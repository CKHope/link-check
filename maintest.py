import streamlit as st
import pandas as pd
import aiohttp
import asyncio
import time

async def check_link_availability_async(session, url):
    start_time = time.time()
    try:
        async with session.get(url, allow_redirects=True) as response:
            # Additional checks for user-friendly display could be added here
            elapsed_time = time.time() - start_time
            return response.status, response.url, elapsed_time
    except aiohttp.ClientResponseError as e:
        # Handle 404 status by retrying after a short delay
        if e.status == 404:
            st.warning(f"Link returned a 404 status. Retrying after a short delay...")
            await asyncio.sleep(5)
            # Retry the check after the delay
            return await check_link_availability_async(session, url)
        else:
            elapsed_time = time.time() - start_time
            return str(e), None, elapsed_time

async def check_links_async(links, max_threads=20):
    async with aiohttp.ClientSession() as session:
        tasks = [check_link_availability_async(session, link) for link in links]
        return await asyncio.gather(*tasks, return_exceptions=True)

def main():
    st.title('Link-Checker Results')

    # File uploader for Excel file
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Load the Excel file into a pandas DataFrame
        df = pd.read_excel(uploaded_file)

        # Extract the links from the 'link' column
        all_links = df['link'].tolist()

        try:
            # Introduce progress bar for link checking
            progress_bar = st.progress(0.0)
            links_count = len(all_links)

            with st.spinner('Checking links...'):
                elapsed_times = []
                for i, link in enumerate(all_links, start=1):
                    result, final_url, elapsed_time = await check_link_availability_async(all_links, max_threads=20)
                    elapsed_times.append(elapsed_time)

                    # Update progress bar
                    progress_percentage = i / links_count
                    progress_bar.progress(progress_percentage)

                # Convert the results to a DataFrame for easy display
                results_df = pd.DataFrame(result, columns=['Status Code', 'Final URL', 'Elapsed Time'])

                # Display progress bar for saving results
                with st.spinner('Saving results...'):
                    results_df.to_excel('link_checker_results.xlsx', index=False)

                # Display the results using Streamlit
                st.subheader('Summary:')
                st.write(f"Total Links: {len(all_links)}")
                st.write(f"Successful Checks: {results_df['Status Code'].between(200, 399).sum()}")
                st.write(f"Failed Checks: {results_df['Status Code'].lt(200).sum() + results_df['Status Code'].ge(400).sum()}")
                st.write(f"Average Elapsed Time per Link: {sum(elapsed_times) / len(elapsed_times):.4f} seconds")

                st.subheader('Detailed Results:')
                st.dataframe(results_df)

        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    main()
