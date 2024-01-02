import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import schedule
import datetime
import string
import json
import nltk
import threading
from urllib import robotparser
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('omw-1.4')
from nltk import pos_tag
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker

def check_robot_txt(url):
    """
    To check the robot.txt file to follow the rules.
"""
    robot = robotparser.RobotFileParser()
    robot.set_url(url + "/robots.txt")  # To append the robots.txt to the base url to access the robots.txt file
    robot.read()

    # To check if web scrapping is allowed for the given seed url 
    return robot.can_fetch("*", url)

def create_csv_file():
    """ 
    To create a .csv file to store all the scrapped records
"""
    database = pd.DataFrame(columns=['Title', 'Link', 'AuthorProfiles',  'DateOfPublication'])
    database.to_csv('cgl_database.csv', index=False)

def get_page_count(base_url):
    """ To find the total no of pages to be scrapped that has research outputs
"""
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    pagination = soup.select_one('.pages ul')
    if pagination:
        page_links = pagination.select('li a.step')  # Select all <a> tags with class="step"
        total_pages = len(page_links)

        # to check if the last page has the 'nextLink' class which indicates that it is not the last page.
        is_last_page = pagination.select_one('li.next a.nextLink')
        if is_last_page:
            total_pages += 1

        return total_pages
    return 1  # Only one page available if pagination not found


def scrap(url):
    """ This function fetches the research publication details from the given url
"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    papers = soup.select('div.rendering_researchoutput_portal-short')
    for paper in papers:
        # To extract the title of each publications and their link
        title_elem = paper.select_one('h3.title a')
        paper_title = title_elem.get_text(strip=True)
        paper_link = title_elem['href']
        # Initialize a dictionary to store author names as keys and their profile links as values
        author_profiles_dict = {}
        # To extract publications of CGL authors, 
        cgl_authors = paper.select('a.link.person')

        # If there are authors with links, process the record, as only cgl authors have profile links
        if cgl_authors:
            # Create a list of dictionaries to hold author details
            authors_list = []
            # # To extract author names with their profile links
            for author in cgl_authors:
                author_name = author.get_text(strip=True)
                author_profile_link = author['href']
                
                # To Create a dictionary for the current author
                author_dict = {'name': author_name, 'link': author_profile_link}
                authors_list.append(author_dict)
            authors_json = json.dumps(authors_list)

            # Extract the date  of publication
            date_of_publication = paper.select_one('span.date').get_text(strip=True)

            # Create a new DataFrame with the data to be appended
            new_data = pd.DataFrame({'Title': [paper_title],
                                     'Link': [paper_link],
                                     'AuthorProfiles': [authors_json],
                                     'DateOfPublication': [date_of_publication]})

            # To load the existing .csv file data
            existing_data = pd.read_csv('cgl_database.csv')

            # To concatenate the new data that is scrapped to existing data
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)

            # To save the updated record to .csv file
            updated_data.to_csv('cgl_database.csv', index=False)

            yield paper_title, paper_link, authors_list, date_of_publication


def update_csv(database):
    current_data = pd.read_csv(database)
    return current_data



def read_csv_file():
    data = pd.read_csv('cgl_database.csv')
    return data

def tokenize_text(txt):
    txt = txt.lower()
    txt = txt.translate(str.maketrans('', '', string.punctuation))
    # Remove stop words
    stop_word = stopwords.words("english")
    lemmatizer = WordNetLemmatizer()
    tkns = nltk.word_tokenize(txt)
    x = ""
    for each in tkns:
        if each not in stop_word:
            x += lemmatizer.lemmatize(each, fwpt(each)) + " "
    return x
    
def fwpt(word):
    tag = pos_tag([word])[0][1][0].upper()
    hash_tag = {"V": wordnet.VERB, "R": wordnet.ADV,"N": wordnet.NOUN,"J": wordnet.ADJ}         
    return hash_tag.get(tag, wordnet.NOUN)


def preprocess_df(df):
    df.Title = df.Title.apply(tokenize_text)
    df['AuthorProfiles'] = df.AuthorProfiles.str.lower()
    df.DateOfPublication = df.DateOfPublication.apply(tokenize_text)
    return df

def construct_inverted_index(df, index):
    for x in range(len(df)):
        inpt = df.loc[x,:]
        words = inpt.Title.split()
        for word in words:
            if word in index.keys():
                if inpt.name not in index[word]:  
                    index[word].append(inpt.name)
            else:
                index[word] = [inpt.name]
    return index
    
def split_query(terms):
    each = tokenize_text(terms)
    return each.split()

def union(lists):
    union = list(set.union(*map(set, lists)))
    union.sort()
    return union

def intersection(lists):
    intersect = list(set.intersection(*map(set, lists)))
    intersect.sort()
    return intersect

def vertical_search_engine(scrapped_data, query, index):
    query_split = split_query(query)
    retrieved = []
    for word in query_split:
        if word in index.keys():
            retrieved.append(index[word])
                    
    # Ranked Retrieval
    if len(retrieved)>0:
        high_ranked_result = intersection(retrieved)
        low_ranked_result = union(retrieved) 
        print("High Ranked:", high_ranked_result )
        print("Low Ranked:", low_ranked_result )
        c = [id for id in low_ranked_result if id not in high_ranked_result]      
        high_ranked_result.extend(c)
        result = high_ranked_result
    else:
        result = []  # When there is no any search result empty list is returned
    
    return result

def find_total_noofauthors(scrapped_data_list):
    # To store the unique authors from the scrapped data
    unique_authors = set()
    # To iterate through all the scrapped records
    for scrapped_record in scrapped_data_list:
        # To convert the 'AuthorProfiles' string to list of dictionaries
        authors_json = scrapped_record['AuthorProfiles']
        author_profiles_list = json.loads(authors_json)

        # To take the set of unique author names
        for author_profile in author_profiles_list:
            unique_authors.add(author_profile['name'])

    # To calculate the total no of unique authors 
    total_authors = len(unique_authors)

    # To count the no of publications for each author
    author_publications_count = {}
    for scrapped_record in scrapped_data_list:
        authors_json = scrapped_record['AuthorProfiles']
        author_profiles_list = json.loads(authors_json)

        for author_profile in author_profiles_list:
            author_name = author_profile['name']
            author_publications_count[author_name] = author_publications_count.get(author_name, 0) + 1

    # To print the number of publications for each author
    for author_name, num_publications in author_publications_count.items():
        print(f" Author Name: {author_name}, {num_publications} publications")

    # To find the author with maximum no of publications
    max_publications_author = max(author_publications_count, key=author_publications_count.get)

    return total_authors, max_publications_author, author_publications_count


def get_current_date_time():
    """
    To get the current date and time.
"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")




