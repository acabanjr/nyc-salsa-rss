import os
import requests
import re
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Target URL
URL = "https://www.salsavida.com/guides/new-york/new-york-city/socials/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_and_create_feed():
    print("Fetching page...")
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch page: {e}")
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
    
    seen_html_blocks = set()
    seen_events = set()
    events_count = 0
    
    # Grab all standard container boxes on the page
    containers = soup.find_all(['div', 'article', 'li'])
    
    for card in containers:
        try:
            # 1. Prevent processing the exact same HTML box twice (solves nested tags)
            card_id = id(card)
            if card_id in seen_html_blocks:
                continue
                
            text = card.text.strip()
            
            # THE TITANIUM FILTER
            has_time = re.search(r'\d{1,2}:\d{2}\s?[AaPp][Mm]', text)
            has_year = re.search(r'202\d', text)
            has_ny = "New York" in text
            
            if not (has_time and has_year and has_ny) or len(text) > 800:
                continue
                
            # If it passes the filter, mark this HTML block as read
            seen_html_blocks.add(card_id)
            
            # Find the title
            links = card.find_all('a')
            event_link = None
            title = None
            
            for l in links:
                l_text = l.text.strip()
                l_href = l.get('href', '')
                if not l_text:
                    continue
                title = l_text
                event_link = l_href
                break
                
            if not title:
                heading = card.find(['h2', 'h3', 'h4', 'strong'])
                if heading:
                    title = heading.text.strip()
            
            if not title or len(title) < 3:
                continue
                
            # 2. Extract the specific Date to handle recurring weekend events
            date_match = re.search(r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s[A-Z][a-z]{2}\s\d{1,2},\s202\d', text)
            event_date = date_match.group(0) if date_match else "UnknownDate"
            
            # Create a unique key (e.g., "LVG Salsa Social-Sunday, Jun 28, 2026")
            unique_event_key = f"{title}-{event_date}"
            
            # 3. Final deduplication check using our new specific key
            if unique_event_key in seen_events:
                continue
            seen_events.add(unique_event_key)
                
            # Clean up the link URL
            link = event_link if event_link else URL
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
            elif not link.startswith('http'):
                link = URL
                
            desc = " ".join(text.split())
            img_element = card.find('img')
            img_url = img_element['src'] if img_element and img_element.has_attr('src') else None
            
            # Add to RSS feed using the unique key as the RSS ID
            fe = fg.add_entry()
            fe.id(link + "-" + unique_event_key.replace(" ", ""))
            fe.title(f"{title} ({event_date})") # Added date to the title so it's clear in your reader!
            fe.link(href=link)
            fe.description(desc)
            
            if img_url and img_url.startswith('http'):
                fe.enclosure(img_url, 0, 'image/jpeg')
                
            events_count += 1
                
        except Exception as e:
            continue

    # Save the finished RSS feed
    if events_count > 0:
        fg.rss_file('salsa_feed.xml', pretty=True)
        print(f"Successfully generated salsa_feed.xml with {events_count} uniquely verified events!")
    else:
        print("Warning: No events found matching the criteria.")

if __name__ == "__main__":
    scrape_and_create_feed()
