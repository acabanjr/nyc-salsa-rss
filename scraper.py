import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Target URL
URL = "https://www.salsavida.com/guides/new-york/new-york-city/socials/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_and_create_feed():
    print("Fetching page...")
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize the RSS Feed Generator
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("NYC Salsa Socials - Salsa Vida")
    fg.author({'name': 'Salsa RSS Bot'})
    fg.link(href=URL, rel='alternate')
    fg.description("Automated RSS feed for upcoming Salsa Socials in New York City.")
    fg.language('en')
    
    # Target all link/anchor elements or container divs that might represent an event
    # We search broadly and filter out non-event blocks inside the loop
    events = soup.find_all(['div', 'article', 'a'])
    seen_titles = set()
    
    for event in events:
        try:
            # 1. Try to find a title element safely
            title_element = event.find(['h3', 'h4', 'h2', 'p'])
            if not title_element:
                continue
                
            title = title_element.text.strip()
            
            # Skip empty titles, short fragments, or common navigation items
            if not title or len(title) < 4 or title in ["Home", "Events", "News", "Articles", "Videos", "Shop", "Share Event"]:
                continue
                
            # Prevent duplicate entries in the same feed run
            if title in seen_titles:
                continue
            
            # 2. Extract Link safely
            link = URL
            link_element = event.find('a') if not event.name == 'a' else event
            if link_element and link_element.has_attr('href'):
                link = link_element['href']
                
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
            elif not link.startswith('http'):
                continue # Skip if it isn't a valid link
                
            # 3. Extract Description text safely
            desc = event.text.strip().replace('\n', ' ')
            # Clean up double spaces
            desc = " ".join(desc.split())
            
            # 4. Extract Image safely if available
            img_element = event.find('img')
            img_url = None
            if img_element and img_element.has_attr('src'):
                img_url = img_element['src']
            
            # 5. Add to RSS feed
            fe = fg.add_entry()
            fe.id(link + "-" + title.replace(" ", ""))
            fe.title(title)
            fe.link(href=link)
            fe.description(desc if desc else f"Salsa event: {title}")
            
            if img_url and img_url.startswith('http'):
                fe.enclosure(img_url, 0, 'image/jpeg')
                
            seen_titles.add(title)
                
        except Exception as e:
            # If any single item fails, log it and keep moving instead of breaking the whole app
            print(f"Skipping an item due to a minor error: {e}")
            continue

    # Save the finished RSS feed to a file
    if len(seen_titles) > 0:
        fg.rss_file('salsa_feed.xml', pretty=True)
        print(f"Successfully generated salsa_feed.xml with {len(seen_titles)} events!")
    else:
        print("Warning: No events were found. Check if the page layout changed radically.")

if __name__ == "__main__":
    scrape_and_create_feed()
