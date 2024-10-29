import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qs
from bs4 import BeautifulSoup
from collections import defaultdict, Counter


ALLOWED_DOMAINS = {
    "ics.uci.edu",
    "cs.uci.edu",
    "informatics.uci.edu",
    "stat.uci.edu",
    "today.uci.edu"
}
ALLOWED_PATH_PREFIX = "today.uci.edu/department/information_computer_sciences"
LOW_INFO_THRESHOLD = 50  # Minimum words required to consider a page informative
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", 
    "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", 
    "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", 
    "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", 
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", 
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", 
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", 
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", 
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", 
    "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", 
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

unique_urls = set()
longest_page_url = None
max_word_count = 0
word_frequencies = defaultdict(int)
subdomain_counts = defaultdict(int)

def tokenize(text):
    tokens = []
    word = ""
    for char in text:
        if ('a' <= char <= 'z') or ('A' <= char <= 'Z') or ('0' <= char <= '9'):
            word += char.lower()
        else:
            if word:
                tokens.append(word)
                word = ""
    if word:
        tokens.append(word)
    return tokens

def compute_word_frequencies(tokens):
    frequencies = defaultdict(int)
    for token in tokens:
        frequencies[token] += 1
    return dict(frequencies)


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Check if the response status is not OK
    if resp.status != 200:
        print(f"Skipping {url}. Status code: {resp.status}")
        return []
    
    if not resp.raw_response or not resp.raw_response.content:
        print(f"Skipping {url}. No content available.")
        return []
    
    content = resp.raw_response.content.decode('utf-8', errors='ignore')
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check meta tags for 'robots' to filter out pages that shouldn't be indexed
    meta_robots = soup.find('meta', attrs={'name': 'robots'})
    if meta_robots:
        content_value = meta_robots.get('content', '').lower()
        if 'noindex' in content_value or 'nofollow' in content_value:
            print(f"Skipping {url}: Marked with noindex or nofollow.")
            return []
    
    body = soup.find('body')
    if not body:
        print(f"Skipping {url}: No Body tags found")
        return []
    text = body.get_text(separator=' ')
    tokens = tokenize(text)

    # Check if this page is the longest so far
    update_longest_page(url, tokens)
    update_word_frequencies(tokens)
    track_unique_url_and_subdomain(url)

    if len(tokens) < LOW_INFO_THRESHOLD:
        print(f"Skipping {url}: Low infomative pages).")
        return []  # Skip low-content pages

    extracted_links = set()
    # find all a tags copntain href attribute. Represent hyperlinks to other pages.
    for tag in soup.find_all('a', href=True): 
        href = tag.get("href")
        full_url = urljoin(resp.raw_response.url, href) # Convert relative URLs to absolute
        defragmented_url, _ = urldefrag(full_url)  # Remove URL fragments

        if is_valid(defragmented_url):
            extracted_links.add(defragmented_url)

    return list(extracted_links)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check if the URL belongs to one of the allowed domains
        if not any(domain in parsed.netloc for domain in ALLOWED_DOMAINS):
            return False
        
        # For today.uci.edu, restrict to specific path
        if "today.uci.edu" in parsed.netloc and not parsed.path.startswith(f"/{ALLOWED_PATH_PREFIX}"):
            return False
        
        if contains_sortable_view_pattern(parsed):
            print(f"Skipping {url}: Detected sortable view pattern.")
            return False
        
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
        
        trap_pattern = (
            r"(calendar|events|login|sign[-_]?up|register|session|cart|view|edit|"
            r"page=\d+|facebook\.com|news|version|.json|entries|ooad)"
        )
        if re.search(trap_pattern, url, re.IGNORECASE):
            print(f"Skipping {url}: Trap pattern found")
            return False
        
        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def contains_sortable_view_pattern(parsed):
    query_params = parse_qs(parsed.query)
    # Example: Skip URLs with sortable query parameters like ?C=N;O=D
    sortable_patterns = {"C", "O"}  # Common keys indicating sortable views
    return any(key in sortable_patterns for key in query_params)

def update_longest_page(url, tokens):
    global longest_page_url, max_word_count
    word_count = len(tokens)
    if word_count > max_word_count:
        max_word_count = word_count
        longest_page_url = url

def update_word_frequencies(tokens):
    global word_frequencies
    for token in tokens:
        if token not in STOP_WORDS:
            word_frequencies[token] += 1

def track_unique_url_and_subdomain(url):
    """Track unique URLs and subdomain counts."""
    global unique_urls, subdomain_counts

    defragmented_url, _ = urldefrag(url)

    if defragmented_url in unique_urls:
        return

    unique_urls.add(defragmented_url)

    # Extract and update subdomain counts if under uci.edu
    parsed = urlparse(defragmented_url)
    if parsed.hostname and parsed.hostname.endswith(".uci.edu"):
        subdomain_counts[parsed.hostname] += 1

def generate_report():
    print(f"Total unique pages found: {len(unique_urls)}")
    if longest_page_url:
        print(f"Longest page: {longest_page_url} with {max_word_count} words")
    common_words = Counter(word_frequencies).most_common(50)
    print("Top 50 most common words:")
    for word, freq in common_words:
        print(f"{word}: {freq}")
    
    print("\nSubdomains found:")
    for subdomain, count in sorted(subdomain_counts.items()):
        print(f"{subdomain}, {count}")