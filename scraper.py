import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup

def scraper(url, resp):
    print(f"Visiting {url}")

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
        return []  # Skip processing if the page is not accessible

    links_list = []
    try:
        content = resp.raw_response.content
        soup = BeautifulSoup(content, 'html.parser')


        for tag in soup.find_all('a', href=True): # find all a tags copntain href attribute. Represent hyperlinks to other pages.
            href = tag['href']

            joined_url = urljoin(url, href) # Handle relative URLs by joining them with the base URL
            clean_url, _ = urldefrag(joined_url) # Remove fragment from the URL (e.g., #section1)

            links_list.append(clean_url)

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
