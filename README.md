Vertical Search Engine CGL


Coventry University CGL Vertical Search Engine Project
Description
This project develops a vertical search engine tailored to retrieve academic articles from Coventry University's Centre for Global Learning. 
It involves web crawling to collect data such as publication titles, links, author information, and publication dates, which are stored in a database. The process includes:

Data Collection: Using BeautifulSoup and Python, the system scrapes and stores details from specific URLs. The focus is on publications by CGL authors.

Data Preprocessing: Includes text normalization, punctuation removal, stop word elimination, POS tagging, and lemmatization.

Scheduled Crawling: A crawler set up to run weekly, updating the index with fresh data.

Indexing: Involves constructing an inverted index for efficient data retrieval.

Query Processing: The system employs preprocessing and Boolean retrieval techniques to rank and retrieve relevant documents based on user queries.

Django Integration: The backend is integrated with Django for web functionality, including a user-friendly interface for searching academic journals.

Technologies Used
Python
BeautifulSoup
Django
Scheduled Crawling Techniques
Inverted Indexing
Natural Language Processing
