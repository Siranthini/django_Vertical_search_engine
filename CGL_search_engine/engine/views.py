
from django.shortcuts import render
from .search_engine import check_robot_txt, create_csv_file, tokenize_text
from .search_engine import get_page_count, scrap,find_total_noofauthors
from .search_engine import read_csv_file, construct_inverted_index, preprocess_df
from .search_engine import vertical_search_engine, get_current_date_time
import pandas as pd
import json
import time
import schedule
import datetime
import threading



def home(request):
    # To do the crawling, preprocessing and indexing
    seed_url = 'https://pureportal.coventry.ac.uk/en/organisations/centre-global-learning'
    if not check_robot_txt(seed_url): 
        print("Web scrapping is not allowed")
        return
    schedule_crawler(seed_url, home)
    base_url = seed_url + "/publications/" # This link has all the publications details which is our area of interest
    create_csv_file()    
    # To get the total no of pages that needs to be scrapped
    total_pages = get_page_count(base_url)
    start_page = 0
    end_page = total_pages - 1
    for current_page in range(start_page, end_page + 1):
        if current_page == 0:
            page_url = base_url
        else:
            page_url = f"{base_url}?page={current_page}" # As all publications are found in base_url with page no appended.
        page_data = list(scrap(page_url))

    # Read the CSV file and display the data
    scrapped_data = read_csv_file()
    original_df = scrapped_data.copy() # To preserve the original data before preprocessing
    print("Raw Data:", original_df)

    preprocessed_df = preprocess_df(scrapped_data)
    print("Preprocessed Data:", preprocessed_df)

    # Construct the index
    indexes = construct_inverted_index(df=preprocessed_df, index={})

    print("Constructed Index:", indexes)

    # To Store the data in the session so that they can be accessed outside this function
    request.session['scrapped_data'] = scrapped_data.to_dict(orient='records')
    request.session['indexes'] = indexes
    request.session['original_data'] = original_df.to_dict(orient='records')

    # Render the home.html template and pass the required data
    return render(request, 'home.html', {'indexes': indexes})

def search_query(request):
    # Get the user's query from the form
    user_query = request.GET.get('query', '')
    print("User Query :", user_query)
    processed_query = tokenize_text(user_query) # To preprocess the query
    print("Preprocessed Query:", processed_query)
    
    # To access the data that is in session and to convert it back to a dataframe
    scrapped_data_list = request.session.get('scrapped_data', [])
    indexes = request.session.get('indexes', {})
    df_data_list = request.session.get('original_data', [])
    scrapped_data = pd.DataFrame(scrapped_data_list)
    df = pd.DataFrame(df_data_list)

    start_time = time.time() # To record the fetching time, Timer is started

    # To fetch the relevant publications
    search_result = vertical_search_engine(scrapped_data, query=processed_query, index=indexes)
    search_result_data = []

    # To convert 'AuthorProfiles' strings back to a list of dictionaries
    for doc_index in search_result:
        document_details = df.loc[doc_index].to_dict()
        authors_json = document_details['AuthorProfiles']
        author_profiles_list = json.loads(authors_json)
        document_details['Authors_Profile'] = author_profiles_list
        search_result_data.append(document_details)

    # To calculate total number of CGL authors, author with maximum publications, and author publications count
    total_authors, max_publications_author, author_publications_count = find_total_noofauthors(scrapped_data_list)
    print("Total no of CGL Authors:", total_authors)
    print(f"The author having maximum no of publications is: {max_publications_author}, {author_publications_count[max_publications_author]} publications")
    end_time = time.time() # to keep track of the total time taken to fetch the publications
    total_time = end_time - start_time
    formatted_time = "{:.2f}(sec)".format(total_time)
    print("Total fetching time:", formatted_time)

    return render(request, 'result.html', {'query': user_query, 'search_result': search_result_data, 'search_time': formatted_time})

def schedule_crawler(seed_url, web_scrapping_function):
    # Schedule the main function to run once a week
    schedule.every().week.do(web_scrapping_function)

    # To Get the current crawled date and time 
    current_crawled_time = get_current_date_time()
    print(f"Data crawled at {current_crawled_time}")

    # To get the next run time of the scheduled job
    next_run = schedule.next_run()
    next_run_str = next_run.strftime('%Y-%m-%d %H:%M:%S')
    print(f"Next crawl scheduled at {next_run_str}")
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    # To Start the scheduler in a separate thread
    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True
    thread.start()