import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from collections import defaultdict

# dictionary containing the frequency of all the tokens
frequency_dict = defaultdict(int)

# dictionary containing the frequency of all the subdomains
subdomain_dict = defaultdict(int)

# contains the name and word count of the url with the longest page
longest_page = {"url": "", "word_count": 0}

# contains a list of all of the unique urls
unique_urls = set()

# list of all the stop words that should not be added to the frequency dictionary
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


# this is my tokenize function from project 1 that I tinkered a bit to better fit 
# the purpose of this assignment. the content of the url page is passed into it
def tokenize(text_content: str) -> list:
    tokens_list = []
    word = ''
    for char in text_content.lower():
        if ('a' <= char <= 'z') or ('0' <= char <= '9'):
            word += char
        else:
            if word:
                tokens_list.append(word)
                word = ''
    if word: 
        tokens_list.append(word)
    return tokens_list


# computes the word frequencies of the tokens picked from the url page
# puts it in the frequency dictionary
def computeWordFrequencies(tokens: list):
    # adding token and their frequencies in dictionary
    for token in tokens:
        if token in frequency_dict and token not in stop_words:
            frequency_dict[token] += 1
        else:
            frequency_dict[token] = 1

    

# this function sorts the frequency dictionary from highest frequency to lowest frequency
# it then only gets the top 50 most frequent words
def get_top_50_words():
    # gets 50 most common words sorted by frequency
    sorted_words = sorted(frequency_dict.items(), key=lambda item: (-item[1], item[0]))
    return sorted_words[:50]


# didnt change
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
    
    # initialize list of hyprelinks
    hyper_set = set()

    # if status is not 200 return empty list
    if resp.status != 200 or resp.raw_response is None:
        return list(hyper_set)

    # setting up check to see if the page is unresponsive
    error_messages = [
        "this page isn't working",
        "redirected you too many times",
        "err_too_many_redirects",
        "too many redirects", "under construction",
        "don't have permission",
        "server IP address could not be found",
        "log in", "privileges are required",
        "sign in", "can't be reached",
        "access denied",
        "restricted access", "required permissions",
        "account required",
        "you must be logged in",
        "error", "no longer exists", "not found", "having trouble",
        "not logged in", "version", "no events"
    ]

    # Skip if error or login is required
    content = resp.raw_response.content.decode('utf-8', errors='ignore') 
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(separator=' ')

    for err in error_messages:
        if err in text.lower():
            return list(hyper_set)


    # use beautiful soup to get content of the URL
    content = resp.raw_response.content
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(separator=' ')

    # tokenize the content in the URL and add them to the dictionary
    tokens = tokenize(text)
    computeWordFrequencies(tokens)

    # if the page doesn't have a lot of content just ignore it
    if len(tokens) < 50:
        return list(hyper_set)
    
    # check to see if its the longest page
    if len(tokens) > longest_page["word_count"]:
        longest_page.update({"url": url, "word_count": len(tokens)})

    # gets the hyperlink
    tags = soup.find_all('a', href=True)
    for link in tags:
        href = link.get('href')
        full_url = urljoin(resp.raw_response.url, href)

        # get rid of the fragments
        parsed_url = urlparse(full_url)
        unique_url = parsed_url._replace(fragment='').geturl()

        # check again if the url is valid and also add to the list of subdomains
        if is_valid(unique_url):
            hyper_set.add(unique_url)
            unique_urls.add(unique_url)
            domain = parsed_url.netloc
            if "uci.edu" in domain:
                subdomain = domain if domain.endswith("uci.edu") else ""
                if subdomain:
                    if subdomain in subdomain_dict:
                        subdomain_dict[subdomain] += 1
                    else:
                        subdomain_dict[subdomain] = 1
    return list(hyper_set)  





def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    # valid domains
    domains = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", "today.uci.edu/department/information_computer_sciences"]
    
    # some things to filter out
    unwanted_keywords = [
    "do=", 
    "action=", 
    "date=",
    "upload",
    "download", 
    "ical", 
    "login", 
    "password", 
    "export", 
    "attachment", 
    "share=",
    "format=",
    "makefile", "calendar"
    ] 

    # dead url patterns
    dead_url_patterns = [
        r".*404.*",
        r".*not-found.*",
        r".*error.*",
        r".*page-not-found.*",
        r".*invalid.*"
    ]

    

    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not any(parsed.netloc.endswith(domain) for domain in domains):
            return False
        
        if any(keyword in parsed.path or keyword in parsed.query for keyword in unwanted_keywords):
            return False
        
        if any(re.search(pattern, url) for pattern in dead_url_patterns):
            return False
        
        # added more things to check in regex and also made it check if any of these things were in the query or path
        return (
            not re.match(r".*\.(calendar|cart|view|edit|facebook.com|.json|ooad|format=|makefile|date=|share=|do=|action=|upload|download|ical|login|password|export|attachment)", parsed.query.lower()) and
            not re.match(r".*\.(calendar|cart|view|edit|facebook.com|.json|ooad|format=|makefile|date=|share=|do=|action=|upload|download|ical|login|password|export|attachment)", parsed.path.lower()) and
            not re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                r"|png|tiff?|mid|mp2|mp3|mp4"
                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                r"|epub|dll|cnf|tgz|sha1|cpp|h|cc|php|bw|cnt|bam"
                r"|thmx|mso|arff|rtf|jar|csv|txt|defs|inc|odc|sas|ppsx"
                r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", 
                parsed.query.lower()) and 
            not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|cpp|h|cc|defs|inc|odc|sas|ppsx"
            + r"|thmx|mso|arff|rtf|jar|csv|txt|php"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()))

    except TypeError:
        print ("TypeError for ", parsed)
        raise
