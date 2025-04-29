import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse

POLITE = 1.0
MIN_CHARS = 2000
MIN_WORDS = 200

last_requests = dict()
seen = set()

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    try:
        if resp.status == 200:
            # Be polite
            be_polite(url)

            # Parse
            soup = BeautifulSoup(resp.raw_response.content, "html.parser")

            if is_content(soup):
                links = []
                for a_tag in soup.find_all("a", href=True):
                    links.append(a_tag["href"])
            
                return links
            
            else:
                return []
        else:
            print(resp.error)
            return []
        
    except Exception as e:
        print(f"ERROR: {e}")


def is_valid(url):
    """
    Decide whether to crawl this url or not. 
    If you decide to crawl it, return True; otherwise return False.
    There are already some conditions that return False.
    """
    try:
        # Remove fragment 
        if '#' in url:
            url = url.split('#')[0]
       
        # check if seen
        if url in seen:
            return False
        else: 
            seen.add(url)
            
        # Check if allowed
        allowed = [
            r".*\.ics\.uci\.edu.*",
            r".*\.cs\.uci\.edu.*",
            r".*\.informatics\.uci\.edu.*",
            r".*\.stat\.uci\.edu.*",
            r"today\.uci\.edu/department/information_computer_sciences/.*" 
        ]
        if not any(re.match(pattern, url) for pattern in allowed):
            return False

        # Must be http or https
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        # Check if not allowed
        skip_extensions_re = re.compile(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            r"|png|tiff?|mid|mp2|mp3|mp4"
            r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1"
            r"|thmx|mso|arff|rtf|jar|csv"
            r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",
            re.IGNORECASE
        )
        if skip_extensions_re.match(parsed.path):
            return False

        return True

    except TypeError:
        print("TypeError for", url)
        raise


def be_polite(url):
    domain = urlparse(url).netloc   
    current = time.time()
    if domain in last_requests:
        diff = current - last_requests[domain]
        if diff < POLITE:
            time.sleep(POLITE - diff)
    last_requests[domain] = time.time()


def is_content(soup):
    for element in soup.findAll(['script', 'style']):
        element.extract()

    webtext = soup.get_text()
    space_delimited_text = re.sub('\s+',' ',webtext)

    # Reject if less char than lower bound
    if len(space_delimited_text) >  MIN_CHARS and len(space_delimited_text.split()) > MIN_WORDS:
        # Gather stats
        get_stats(soup)
        return True
    
    else:
        return False


def get_stats(soup):

    pass 
