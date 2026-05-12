import requests
from bs4 import BeautifulSoup
import os
import time
import urllib.parse
from urllib.parse import urljoin, urlparse
import csv

# ================== কনফিগারেশন ==================
BASE_URL = "https://tll.com.bd"
DOMAIN = "tll.com.bd"
SAVE_FOLDER = "tll_local_website"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

visited = set()
session = requests.Session()

def get_filename_from_url(url):
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    elif not os.path.splitext(path)[1]:
        path += ".html"
    return os.path.join(SAVE_FOLDER, path)

def download_file(url, save_path):
    try:
        if url in visited:
            return True
        visited.add(url)
        
        print(f"📥 Downloading: {url}")
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
        return False

def fix_links(soup, page_url):
    """সব লিংককে লোকাল পাথে পরিবর্তন"""
    for tag in soup.find_all(['a', 'link', 'script', 'img'], href=True):
        attr = 'href' if tag.name in ['a', 'link'] else 'src'
        old_url = tag.get(attr)
        if not old_url:
            continue
            
        full_url = urljoin(page_url, old_url)
        
        if DOMAIN in full_url or full_url.startswith('/'):
            parsed = urlparse(full_url)
            local_path = parsed.path.strip("/") or "index.html"
            if not os.path.splitext(local_path)[1] and tag.name == 'a':
                local_path += ".html"
            tag[attr] = "/" + local_path  # relative path

def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    
    # CSV থেকে পেজ লিস্ট পড়া
    pages = []
    try:
        with open('tll_all_pages.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            pages = [row['url'] for row in reader]
    except FileNotFoundError:
        print("tll_all_pages.csv না পাওয়া গেছে। শুধু হোমপেজ ডাউনলোড হবে।")
        pages = [BASE_URL]
    
    print(f"মোট {len(pages)} পেজ ডাউনলোড শুরু হচ্ছে...\n")
    
    for url in pages:
        if url in visited:
            continue
            
        local_path = get_filename_from_url(url)
        
        # HTML ডাউনলোড
        if download_file(url, local_path):
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                
                fix_links(soup, url)
                
                # Images, CSS, JS ডাউনলোড
                for tag in soup.find_all(['img', 'link', 'script']):
                    attr = 'src' if tag.name in ['img', 'script'] else 'href'
                    resource_url = tag.get(attr)
                    if resource_url:
                        full_resource = urljoin(url, resource_url)
                        if DOMAIN in full_resource:
                            resource_path = get_filename_from_url(full_resource)
                            resource_path = resource_path.replace(".html", "")
                            if tag.name == 'img' or full_resource.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg')):
                                download_file(full_resource, resource_path)
                                # লোকাল লিংক আপডেট
                                relative = os.path.relpath(resource_path, os.path.dirname(local_path))
                                tag[attr] = relative.replace("\\", "/")
                
                # আপডেটেড HTML সেভ
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                    
            except Exception as e:
                print(f"HTML processing error {url}: {e}")
        
        time.sleep(1)  # সার্ভারকে রেস্ট দিতে
    
    print(f"\n🎉 ডাউনলোড সম্পন্ন!")
    print(f"📁 সবকিছু সেভ হয়েছে: {os.path.abspath(SAVE_FOLDER)} ফোল্ডারে")
    print("ইনডেক্স খুলুন: tll_local_website/index.html")

if __name__ == "__main__":
    main()