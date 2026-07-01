import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime

# 1. Target URL
URL = "https://www.salsavida.com/guides/new-york/new-york-city/socials/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def scrape_and_create_feed():
    # 2. Fetch the webpage html
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 3. Initialize the RSS Feed Generator
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("NYC Salsa Socials - Salsa Vida")
    fg.author({'name': 'Salsa RSS Bot'})
    fg.link(href=URL, rel='alternate')
    fg.description("Automated RSS feed for upcoming Salsa Socials in New York City.")
    fg.language('en')
    
    # 4. Find all event elements
    # Note: If the website layout changes, these class names may need updating.
    events = soup.find_all('div', class_='event-card') or soup.find_all('article')
    
    for event in events:
        try:
            # Extract Title
            title_element = event.find('h3') or event.find('h2')
            if not title_element:
                continue
            title = title_element.text.strip()
            
            # Extract Link
            link_element = event.find('a')
            link = link_element['href'] if link_element else URL
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
                
            # Extract Description (Date, Time, Venue)
            desc = event.text.strip()
            
            # Extract Image if available
            img_element = event.find('img')
            img_url = img_element['src'] if img_element else None
            
            # 5. Create an RSS item for this event
            fe = fg.add_entry()
            fe.id(link + "-" + title)
            fe.title(title)
            fe.link(href=link)
            fe.description(desc)
            
            if img_url:
                fe.enclosure(img_url, 0, 'image/jpeg')
                
        except Exception as e:
            print(f"Skipping an item due to error: {e}")
            continue

    # 6. Save the finished RSS feed to a file
    fg.rss_file('salsa_feed.xml', pretty=True)
    print("Successfully generated salsa_feed.xml")

if __name__ == "__main__":
    scrape_and_create_feed()
