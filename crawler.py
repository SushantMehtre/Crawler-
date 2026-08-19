import requests
from bs4 import BeautifulSoup
import urllib.parse
import random
from typing import List, Dict, Any

# A list of public Redlib proxy instances to rotate through if one is down
REDLIB_INSTANCES = [
    "safereddit.com",
    "reddit.invak.am",
    "redlib.ducks.party",
    "l.opnxng.com",
    "redlib.kittycat.homes",
    "redlib.non-toxic.org"
]

def clean_reddit_url(url: str, domain: str = "safereddit.com") -> str:
    """
    Cleans the Reddit URL and rewrites it to use a public Redlib instance domain.
    """
    # Remove query parameters
    url = url.split('?')[0]
    
    # Replace reddit.com / old.reddit.com with the target proxy domain
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.netloc.lower()
    
    if "reddit.com" in netloc:
        url = parsed._replace(netloc=domain).geturl()
        
    return url

def scrape_reddit(url: str) -> Dict[str, Any]:
    """
    Scrapes a Reddit thread/subreddit by trying multiple public Redlib proxies.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Shuffle instances to distribute load and try different ones on failure
    instances = REDLIB_INSTANCES.copy()
    random.shuffle(instances)
    
    html_content = None
    last_error = None
    successful_url = None
    
    for instance in instances:
        scraped_url = clean_reddit_url(url, domain=instance)
        try:
            print(f"Attempting to scrape from proxy: {scraped_url}")
            response = requests.get(scraped_url, headers=headers, timeout=10)
            response.raise_for_status()
            html_content = response.text
            successful_url = scraped_url
            break # Success!
        except Exception as e:
            print(f"Proxy {instance} failed: {e}")
            last_error = e
            continue
            
    if not html_content:
        # Final desperate attempt: try old.reddit.com directly
        try:
            fallback_url = url.replace("www.reddit.com", "old.reddit.com")
            print(f"Attempting fallback to direct old.reddit: {fallback_url}")
            response = requests.get(fallback_url, headers=headers, timeout=10)
            response.raise_for_status()
            html_content = response.text
            successful_url = fallback_url
        except Exception as e:
            raise ValueError(
                f"Failed to scrape from Reddit or any proxy instances.\n"
                f"Last proxy error: {str(last_error)}\n"
                f"Direct Reddit fallback error: {str(e)}\n\n"
                "Please use the 'Paste Text/HTML' or 'Upload File' option in the sidebar as a fallback."
            )

    soup = BeautifulSoup(html_content, 'html.parser')
    results = {
        'url': url,
        'title': '',
        'texts': []
    }
    
    # Extract Title
    title_el = soup.find('h2', class_=lambda x: x and 'post_title' in x)
    if title_el:
        results['title'] = title_el.get_text(strip=True)
    else:
        title_el = soup.find('title')
        if title_el:
            results['title'] = title_el.get_text(strip=True).replace(" | Redlib", "").replace(" - old.reddit.com", "")
        else:
            results['title'] = "Scraped Reddit Thread"
            
    # Extract Post Body Content (if any)
    post_body_el = soup.find(class_=lambda x: x and 'post_body' in x)
    if not post_body_el and "old.reddit.com" in successful_url:
        # Old reddit body container class
        post_body_el = soup.find('div', class_='usertext-body')
        
    if post_body_el:
        post_text = post_body_el.get_text("\n", strip=True)
        if post_text:
            results['texts'].append(f"Post Content:\n{post_text}")
            
    # Extract Comments (Redlib structure)
    comment_divs = soup.find_all(class_=lambda x: x and 'comment_body' in x)
    
    # Fallback to Old Reddit comments if using old.reddit.com directly
    if not comment_divs and "old.reddit.com" in successful_url:
        comment_divs = soup.find_all('div', class_='usertext-body')
        # Skip the first usertext-body if it's the post body we already got
        if post_body_el in comment_divs:
            comment_divs.remove(post_body_el)

    for i, comment_div in enumerate(comment_divs, 1):
        # Try to find comment author
        author_text = "Unknown"
        comment_wrapper = comment_div.find_parent('div', class_=lambda x: x and 'comment' in x)
        if comment_wrapper:
            author_el = comment_wrapper.find('a', class_=lambda x: x and 'comment_author' in x)
            if author_el:
                author_text = author_el.get_text(strip=True)
        elif "old.reddit.com" in successful_url:
            # Old Reddit author tag search
            entry_wrapper = comment_div.find_parent('div', class_='entry')
            if entry_wrapper:
                author_el = entry_wrapper.find('a', class_='author')
                if author_el:
                    author_text = author_el.get_text(strip=True)
                
        comment_text = comment_div.get_text("\n", strip=True)
        # Avoid duplicating post body in old reddit comments parsing
        if comment_text and not comment_text.startswith("Post Content:"):
            results['texts'].append(f"Comment {i} by {author_text}:\n{comment_text}")
            
    # If no comments or posts were found, maybe it's a listing page (Subreddit)
    if not results['texts']:
        post_divs = soup.find_all('div', class_=lambda x: x and 'post' in x)
        for i, post_div in enumerate(post_divs, 1):
            p_title_el = post_div.find('h2', class_=lambda x: x and 'post_title' in x)
            p_body_el = post_div.find('div', class_=lambda x: x and 'post_body' in x)
            p_author_el = post_div.find('a', class_=lambda x: x and 'post_author' in x)
            
            p_title = p_title_el.get_text(strip=True) if p_title_el else "Untitled"
            p_body = p_body_el.get_text("\n", strip=True) if p_body_el else ""
            p_author = p_author_el.get_text(strip=True) if p_author_el else "Unknown"
            
            content = f"Post {i} (Title: {p_title} | Author: {p_author}):\n{p_body}"
            results['texts'].append(content.strip())
            
    if not results['texts']:
        raise ValueError("Could not find any posts or comments in the scraped HTML page structure.")
        
    return results

if __name__ == "__main__":
    test_url = "https://www.reddit.com/r/Python/comments/1unctej/showcase_thread/"
    try:
        print("Testing crawler via proxy rotation...")
        res = scrape_reddit(test_url)
        print(f"Success! Title: {res['title']}")
        print(f"Extracted {len(res['texts'])} texts/posts/comments.")
    except Exception as e:
        print(f"Test failed: {e}")
