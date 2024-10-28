import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from collections import defaultdict, Counter, deque


# Globals for tracking data
unique_urls = set()
subdomain_counts = defaultdict(int)
word_counter = Counter()
longest_page = {"url": "", "word_count": 0}


LOW_INFO_THRESHOLD = 50  # Minimum words required to consider a page informative
LARGE_FILE_THRESHOLD = 5000  # Max allowable words before skipping large files

def tokenize(text):
    tokens = []
    word = ""
    for char in text:
        if ('a' <= char <= 'z') or ('A' <= char <= 'Z') or ('0' <= char <= '9'):
            word += char.lower()
        else:
            if word:
                tokens.append(word)
                word = ""  # Reset word
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

    links_list = []
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        text = soup.get_text(separator=' ')
        tokens = tokenize(text)

        # Check for low information content
        if len(tokens) < LOW_INFO_THRESHOLD:
            print(f"Skipping {url}: Low information content.")
            return []

        # Avoid very large files with low information value
        if len(tokens) > LARGE_FILE_THRESHOLD:
            print(f"Skipping {url}: File too large.")
            return []
        
        # Update word counter
        word_counter.update(tokens)

        # Track longest page
        if len(tokens) > longest_page["word_count"]:
            longest_page.update({"url": url, "word_count": len(tokens)})

        for tag in soup.find_all('a', href=True): # find all a tags copntain href attribute. Represent hyperlinks to other pages.
            href = tag['href']
            joined_url = urljoin(url, href) # Handle relative URLs by joining them with the base URL
            clean_url, _ = urldefrag(joined_url) # Remove fragment from the URL (e.g., #section1)
            links_list.append(clean_url)

            # Track unique URLs and subdomains
            if clean_url not in unique_urls:
                unique_urls.add(clean_url)
                subdomain = urlparse(clean_url).netloc
                if subdomain.endswith(".uci.edu"):
                    subdomain_counts[subdomain] += 1

    except Exception as e:
        print(f"Error parsing {url}: {e}")

    return links_list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        # Check if URL is allowed
        if not (
            parsed.netloc.endswith(".ics.uci.edu") or
            parsed.netloc.endswith(".cs.uci.edu") or
            parsed.netloc.endswith(".informatics.uci.edu") or
            parsed.netloc.endswith(".stat.uci.edu") or
            (parsed.netloc == "today.uci.edu" and 
             parsed.path.startswith("/department/information_computer_sciences"))
        ):
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

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
