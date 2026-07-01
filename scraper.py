import os
import requests
import re # NEW: We are bringing in Regular Expressions!
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
    events_count = 0
    
    # Find every element that contains the "Share Event" text.
    share_buttons = soup.find_all(lambda tag: tag.name in ['a', 'div', 'button', 'span'] and tag.text and "Share Event" in tag.text)
    
    for btn in share_buttons:
        try:
            # Move up to the closest container box
            card = btn.find_parent(['div', 'article', 'li'])
            if not card:
                continue
                
            text = card.text.strip()
            
            # THE ULTIMATE FILTER: The text MUST contain a time pattern (e.g., 6:00 PM, 10:30AM, 9:00 pm)
            # If there is no time listed, it is a random website link and we skip it instantly.
            if not re.search(r'\d{1,2}:\d{2}\s?[AaPp][Mm]', text):
                continue
            
            # Find the title link inside this card
            links = card.find_all('a')
            event_link = None
            title = None
            
            for l in links:
                l_text = l.text.strip()
                l_href = l.get('href', '')
                
                # Skip the "Share Event" link itself or empty links
                if "Share Event" in l_text or not l_text:
                    continue
                    
                title = l_text
                event_link = l_href
                break
                
            # Fallback if no specific title link was isolated
            if not title:
                heading = card.find(['h2', 'h3', 'h4', 'p'])
                if heading:
                    title = heading.text.strip()
            
            # Final validation check
            if not title or len(title) < 3 or title in seen_titles:
                continue
                
            # Clean up the link URL
            link = event_link if event_link else URL
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
            elif not link.startswith('http'):
                link = URL
                
            # Clean up description text
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
            events_count += 1
                
        except Exception as e:
            print(f"Skipped an item due to parsing error: {e}")
            continue

    # Save the finished RSS feed
    if events_count > 0:
        fg.rss_file('salsa_feed.xml', pretty=True)
        print(f"Successfully generated salsa_feed.xml with {events_count} real events!")
    else:
        print("Warning: No events found matching the strict time criteria.")

if __name__ == "__main__":
    scrape_and_create_feed()
