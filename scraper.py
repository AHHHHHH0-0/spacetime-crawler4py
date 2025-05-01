import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import defaultdict

POLITE = 1.0
MIN_CHARS = 2000
MIN_WORDS = 200

last_requests = dict()
seen = set()
longest_page = {"url": "", "length": 0}
top_50 = defaultdict(int)
subdomains = defaultdict(int)

def scraper(url, resp):
    links = extract_next_links(url, resp)
    #result()
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    try:
        if resp and resp.status == 200 and resp.raw_response and resp.raw_response.content:
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
            if resp:
                print(f"ERROR: {resp.error}")
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
            
        # Check calendar traps
        calendar_patterns = [
            r'calendar',
            r'event',
            r'week=\d+',
            r'month=\d+',
            r'year=\d+'
        ]
        
        if any(re.search(pattern, url.lower()) for pattern in calendar_patterns):
            return False
            
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
    # Get words
    text = soup.get_text()
    words = [word.lower() for word in re.findall(r'\w+', text) if len(word) > 1]
    
    # Longest page
    if len(words) > longest_page["length"]:
        longest_page["url"] = soup.url
        longest_page["length"] = len(words)
    
    # Word frequencies
    for word in words:
        top_50[word] += 1
    
    # Subdomain
    domain = urlparse(soup.url).netloc
    subdomains[domain] += 1


def result():

    stopwords = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
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
        "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", 
        "you've", "your", "yours", "yourself", "yourselves"
    }

    filtered_top_50 = {word: count for word, count in top_50.items() if word not in stopwords}

    print(f"Number of unique pages: {len(seen)}")
    print(f"Longest page: {longest_page['url']}, {longest_page['length']}")
    #print(f"Top 50 Words: {sorted(top_50.items(), key = lambda x: -x[1])[:50]}")
    print(f"Top 50 Words (excluding stopwords): {sorted(filtered_top_50.items(), key=lambda x: -x[1])[:50]}")
    print("Subdomains found in uci.edu domain:")
    for domain, count in sorted(subdomains.items()):
        print(f"{domain}, {count}")
