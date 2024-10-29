import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import defaultdict, Counter
import os


stop_words = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did", 
    "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", 
    "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", 
    "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", 
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", 
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", 
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", 
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", 
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", 
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", 
    "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", 
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", 
    "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", 
    "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", 
    "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", 
    "you're", "you've", "your", "yours", "yourself", "yourselves"
]

# Data structures to track unique pages, word counts, and subdomains
unique_pages = set()
longest_page = ("", 0)  # (URL, word count)
word_frequency = Counter()
subdomain_count = defaultdict(int)

visited_urls = set()

politeness_delay = defaultdict(lambda: 1)  # Default politeness delay of 1 second for each domain

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    global longest_page
    links = set()  # Using a set to automatically handle duplicate URLs

    if resp.status == 200 and resp.raw_response:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")

        # Extract text and count words for longest page
        text = soup.get_text()
        words = [word.lower() for word in re.findall(r"\w+", text) if word.lower() not in stop_words]
        word_count = len(words)

        # Update the longest page information
        if word_count > longest_page[1]:
            longest_page = (url, word_count)

        # Update word frequency
        word_frequency.update(words)

        # Extract all hyperlinks from the page
        for anchor in soup.find_all('a', href=True):
            href = anchor.get('href')
            if href:
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(url, href)

                # Remove fragment part of the URL and normalize
                defragmented_href = normalize_url(absolute_url)

                # Append the cleaned URL to the list of links
                links.add(defragmented_href)

                # Track unique pages and subdomains
                if defragmented_href not in unique_pages:
                    unique_pages.add(defragmented_href)
                    subdomain = parsed_subdomain(defragmented_href)
                    subdomain_count[subdomain] += 1

    return list(links)

def normalize_url(url):
    parsed = urlparse(url)
    # Remove fragment, query, and trailing slash
    clean_url = parsed._replace(fragment='', query='', path=parsed.path.rstrip('/')).geturl()
    return clean_url

def parsed_subdomain(url):
    parsed = urlparse(url)
    return parsed.netloc

def is_valid(url):
    try:
        parsed = urlparse(url)

        # Ensure URL has the correct scheme (http or https)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Avoid URLs with unwanted file extensions
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False

        # Avoid infinite traps such as calendar pages or session IDs
        if re.search(r"calendar|date|sessionid|sort|filter|page=", parsed.query, re.IGNORECASE):
            return False

        # Avoid revisiting previously visited URLs
        if parsed.geturl() in visited_urls:
            return False
        visited_urls.add(parsed.geturl())

        # Check if the URL belongs to the specified domains and paths
        if not re.match(r".*\.((ics|cs|informatics|stat)\.uci\.edu|today\.uci\.edu/department/information_computer_sciences)/.*", parsed.netloc + parsed.path):
            return False

        return True

    except TypeError:
        print("TypeError for ", parsed)
        raise

# Example functions to get data for the report
def get_unique_page_count():
    print(f"Unique pages found: {len(unique_pages)}")
    return len(unique_pages)

def get_longest_page():
    print(f"Longest page URL: {longest_page[0]}, Word count: {longest_page[1]}")
    return longest_page

def get_most_common_words():
    common_words = word_frequency.most_common(50)
    print("50 most common words:")
    for word, count in common_words:
        print(f"{word}: {count}")
    return common_words

def get_subdomain_counts():
    sorted_subdomains = sorted(subdomain_count.items())
    print("Subdomain counts:")
    for subdomain, count in sorted_subdomains:
        print(f"{subdomain}, {count}")
    return sorted_subdomains
