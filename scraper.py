import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


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
    hyper_set = set()

    if resp.status != 200:
        content = resp.raw_response.content.decode('utf-8', errors='ignore')  # Decode bytes to str
        error_messages = [
            "this page isn’t working",
            "redirected you too many times",
            "err_too_many_redirects",
            "too many redirects"
        ]
        if any(err in content.lower() for err in error_messages):
            return list(hyper_set) 
    
    error_messages = [
    "this page isn’t working",
    "redirected you too many times",
    "err_too_many_redirects",
    "too many redirects"
    ]


    content = resp.raw_response.content
    soup = BeautifulSoup(content, "html.parser")
    if len(content) < 1000:
        return list(hyper_set) 

    body = soup.find('body')
    if body:
        text = body.get_text(' | ', strip=True)
        num_text = text.count('|')
        if num_text < 40:
            return list(hyper_set) 

        tags = soup.find_all('a', href=True)
        for link in tags:
            href = link.get('href')
            full_url = urljoin(resp.raw_response.url, href)

            parsed_url = urlparse(full_url)
            unique_url = parsed_url._replace(fragment='').geturl()
            if is_valid(unique_url):
                hyper_set.add(unique_url)

    return list(hyper_set)  

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    domains = [".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", "today.uci.edu/department/information_computer_sciences"]
    
    unwanted_keywords = [
    "do=", 
    "action=", 
    "upload",
    "download", 
    "ical", 
    "login", 
    "password", 
    "export", 
    "attachment", 
    "share="
    ] 

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
        
        return (
            not re.match(r".*\.(share=|do=|action=|upload|download|ical|login|password|export|attachment)", parsed.query.lower()) and
            not re.match(r".*\.(share=|do=|action=|upload|download|ical|login|password|export|attachment)", parsed.path.lower()) and
            not re.match(
                r".*\.(css|js|bmp|gif|jpe?g|ico"
                r"|png|tiff?|mid|mp2|mp3|mp4"
                r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                r"|epub|dll|cnf|tgz|sha1|cpp|h|cc"
                r"|thmx|mso|arff|rtf|jar|csv|txt|defs|inc"
                r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", 
                parsed.query.lower()) and 
            not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|cpp|h|cc|defs|inc"
            + r"|thmx|mso|arff|rtf|jar|csv|txt"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()))

    except TypeError:
        print ("TypeError for ", parsed)
        raise
