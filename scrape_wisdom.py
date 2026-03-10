import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

base_url = "https://www.wisdomlib.org/jyotisha"
output_dir = "./wisdomlib_jyotisha"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def download_page(url, depth=0, max_depth=2):
    if depth > max_depth:
        return
        
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Save current page
        filename = url.split('/')[-1] or "index"
        if not filename.endswith('.html'):
            filename += '.html'
            
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"Downloaded: {url}")
        
        # Find links
        for link in soup.find_all('a', href=True):
            next_url = urljoin(url, link['href'])
            if next_url.startswith("https://www.wisdomlib.org") and "/jyotish" in next_url:
                # Basic protection against infinite loops in this quick script
                if not os.path.exists(os.path.join(output_dir, next_url.split('/')[-1] + '.html')):
                     download_page(next_url, depth + 1, max_depth)
                     
    except Exception as e:
        print(f"Error downloading {url}: {e}")

print("Starting Wisdomlib scrape...")
download_page(base_url)
print("Scrape complete!")
