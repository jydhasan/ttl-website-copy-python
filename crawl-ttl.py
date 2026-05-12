import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import csv
from collections import deque

# ================== কনফিগারেশন ==================
START_URL = "https://tll.com.bd/"
DOMAIN = "tll.com.bd"

# যে লিংকগুলো বাদ দিতে চান (অপশনাল)
EXCLUDE_PATHS = ['/wp-', '/feed', '/comments', '/tag/', '/category/', 'author']

visited = set()
all_pages = []

def is_valid_url(url):
    """চেক করে শুধু এই ডোমেইনের লিংক নেবে"""
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc != DOMAIN and not parsed.netloc.endswith("." + DOMAIN):
        return False
    
    for exclude in EXCLUDE_PATHS:
        if exclude in url:
            return False
    return True

def crawl():
    queue = deque([START_URL])
    
    print("Crawling শুরু হচ্ছে...\n")
    
    while queue:
        current_url = queue.popleft()
        
        if current_url in visited:
            continue
            
        visited.add(current_url)
        
        try:
            print(f"✅ Crawling: {current_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # পেজ টাইটেল সংরক্ষণ
            title = soup.title.string.strip() if soup.title else "No Title"
            all_pages.append({
                'url': current_url,
                'title': title
            })
            
            # সব লিংক খুঁজে বের করা
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(current_url, href)
                
                # শুধু http/https লিংক
                if full_url.startswith(('http://', 'https://')):
                    if is_valid_url(full_url) and full_url not in visited:
                        queue.append(full_url)
            
            time.sleep(1)  # সার্ভারকে overload না করার জন্য
            
        except Exception as e:
            print(f"❌ Error crawling {current_url}: {e}")
    
    # ================== সেভ করা ==================
    # CSV ফাইলে সেভ
    with open('tll_all_pages.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title'])
        writer.writeheader()
        writer.writerows(all_pages)
    
    # টেক্সট ফাইলে সেভ
    with open('tll_all_pages.txt', 'w', encoding='utf-8') as f:
        for page in all_pages:
            f.write(f"{page['title']}\n{page['url']}\n{'-'*80}\n")
    
    print(f"\n🎉 Crawling সম্পন্ন!")
    print(f"মোট পেজ পাওয়া গেছে: {len(all_pages)}")
    print("📁 ফাইল সেভ হয়েছে: tll_all_pages.csv এবং tll_all_pages.txt")

if __name__ == "__main__":
    crawl()