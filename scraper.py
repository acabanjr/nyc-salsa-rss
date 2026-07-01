import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Target URL
URL = "https://www.salsavida.com/guides/new-york/new-york-city/socials/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_and_create_feed():
    print("Fetching page...")
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize the RSS Feed
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("NYC Salsa Socials - Salsa Vida")
    fg.author({'name': 'Salsa RSS Bot'})
    fg.link(href=URL, rel='alternate')
    fg.description("Automated RSS feed for upcoming Salsa Socials in New York City.")
    fg.language('en')
    
    seen_titles = set()
    
    # Target divs and articles that act as containers
    potential_cards = soup.find_all(['div', 'article', 'li'])
    
    for card in potential_cards:
        try:
            text = card.text.strip()
            
            # FILTER: A real event card must have a heading, a link, and mention a time (AM/PM)
            title_element = card.find(['h2', 'h3', 'h4'])
            link_element = card.find('a')
            
            # If it's missing a title, a link, or doesn't look like an event (no AM/PM), skip it!
            # We also ensure the block of text isn't the entire webpage (len < 600)
            if not title_element or not link_element or (" PM" not in text and " AM" not in text) or len(text) > 600:
                continue

            title = title_element.text.strip()
            
            # Skip if we already grabbed this exact event to prevent duplicates
            if title in seen_titles:
                continue
            
            # Extract Link
            link = link_element['href']
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
                
            # Clean up the description text (remove extra line breaks)
            desc = " ".join(text.split())
            
            # Extract Image if available
            img_element = card.find('img')
            img_url = img_element['src'] if img_element and img_element.has_attr('src') else None
            
            # Add to RSS feed
            fe = fg.add_entry()
            fe.id(link + "-" + title.replace(" ", ""))
            fe.title(title)
            fe.link(href=link)
            fe.description(desc)
            
            if img_url and img_url.startswith('http'):
                fe.enclosure(img_url, 0, 'image/jpeg')
                
            seen_titles.add(title)
                
        except Exception as e:
            continue

    # Save the finished RSS feed
    if len(seen_titles) > 0:
        fg.rss_file('salsa_feed.xml', pretty=True)
        print(f"Successfully generated salsa_feed.xml with {len(seen_titles)} actual events!")
    else:
        print("Warning: No events passed the filter. Check if the page layout changed.")

if __name__ == "__main__":
    scrape_and_create_feed()
