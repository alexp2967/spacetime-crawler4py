import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import Counter

crawled_data = {}

def scraper(url, resp):
    # Check for valid response status and content type
    if resp.status == 200 and 'text/html' in resp.raw_response.headers.get('Content-Type', ''):
        crawled_data[url] = resp.raw_response.content
        links = extract_next_links(url, resp)
        valid_links = [link for link in links if is_valid(link)]
        print(f"Processed {url}: {len(valid_links)} valid links found.")  # Debugging statement
        return valid_links
    else:
        print(f"Skipping {url}: Invalid status or content type.")  # Debugging statement
        return []
    
##############################################
def extract_next_links(url, resp):
    links = set()  # Using a set to automatically handle duplicate URLs
    if resp.status != 200:
        print(f"Skipping {url}: Response status is not OK.")
        return list(links)

    content_type = resp.raw_response.headers.get('Content-Type', '')
    if 'text/html' not in content_type:
        print(f"Skipping {url}: Content-Type is not text/html.")
        return list(links)

    charset = re.search(r'charset=([\w-]+)', content_type)
    encoding = charset.group(1) if charset else 'utf-8'

    try:
        content = resp.raw_response.content.decode(encoding, errors='replace')
    except UnicodeDecodeError:
        content = resp.raw_response.content.decode('latin-1')

    soup = BeautifulSoup(content, 'html.parser')
    for link in soup.find_all('a', href=True):
        full_url = urljoin(resp.url, link['href'])
        normalized_url = normalize_url(full_url)  # Normalize URL to remove fragments and clean it up
        links.add(normalized_url)

    return list(links)

def normalize_url(url):
    parsed = urlparse(url)
    clean_url = parsed._replace(fragment='').geturl()
    return clean_url

        
################################################
def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not any(parsed.netloc.endswith(valid_domain) for valid_domain in ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"]):
            return False
        # Further refine to avoid non-relevant content types or very large files if necessary
        if re.search(r".*\.(css|js|bmp|gif|jpeg|jpg|ico|"
                     r"png|tiff|mid|mp2|mp3|mp4|"
                     r"wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|"
                     r"ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|"
                     r"data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|"
                     r"epub|dll|cnf|tgz|sha1|"
                     r"thmx|mso|arff|rtf|jar|csv|"
                     r"rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False
        return True
    except TypeError as e:
        print("TypeError in is_valid for URL:", url, "Error:", e)
        return False


def extract_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ')
    return re.findall(r'\b\w+\b', text.lower())

# Function to update word counts while ignoring stopwords
def update_word_counts(text, word_counts, stopwords):
    words = [word for word in text if word not in stopwords]
    word_counts.update(words)

# Example usage within your crawler after processing each page
stopwords = set(["a", "about", "above", "after", "again", 
                    "against", "all", "am", "an", "and", 
                    "any", "are", "aren't", "as", "at", 
                    "be", "because", "been", "before", "being", 
                    "below", "between", "both", "but", "by", 
                    "can't", "cannot", "could", "couldn't", "did", 
                    "didn't", "do", "does", "doesn't", "doing", 
                    "don't", "down", "during", "each", "few", 
                    "for", "from", "further", "had", "hadn't", 
                    "has", "hasn't", "have", "haven't", "having", 
                    "he", "he'd", "he'll", "he's", "her", 
                    "here", "here's", "hers", "herself", "him", 
                    "himself", "his", "how", "how's", "i", 
                    "i'd", "i'll", "i'm", "i've", "if", 
                    "in", "into", "is", "isn't", "it", 
                    "it's", "its", "itself", "let's", "me", 
                    "more", "most", "mustn't", "my", "myself", 
                    "no", "nor", "not", "of", "off", 
                    "on", "once", "only", "or", "other", 
                    "ought", "our", "ours", "ourselves", "out", "over", 
                    "own", "same", "shan't", "she", "she'd", 
                    "she'll", "she's", "should", "shouldn't", "so", 
                    "some", "such", "than", "that", "that's", 
                    "the", "their", "theirs", "them", "themselves", 
                    "then", "there", "there's", "these", "they", 
                    "they'd", "they'll", "they're", "they've", "this", 
                    "those", "through", "to", "too", "under", 
                    "until", "up", "very", "was", "wasn't", 
                    "we", "we'd", "we'll", "we're", "we've", 
                    "were", "weren't", "what", "what's", "when", 
                    "when's", "where", "where's", "which", "while", 
                    "who", "who's", "whom", "why", "why's", 
                    "with", "won't", "would", "wouldn't", "you", 
                    "you'd", "you'll", "you're", "you've", "your", 
                    "yours", "yourself"])
word_counts = Counter()

for url, html_content in crawled_data.items():
    text = extract_text(html_content)
    update_word_counts(text, word_counts, stopwords)

# To get the 50 most common words after all pages have been processed
most_common_words = word_counts.most_common(50)
print("50 most common words:", most_common_words)
