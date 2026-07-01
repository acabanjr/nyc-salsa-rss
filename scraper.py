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
    events_count = 0
    
    # Strategy: Find every element that contains the "Share Event" text.
    # This represents exactly one unique event card.
    share_buttons = soup.find_all(lambda tag: tag.name in ['a', 'div', 'button'] and tag.text and "Share Event" in tag.text)
    
    for btn in share_buttons:
        try:
            # Move up to the closest container box that holds this specific event's info
            card = btn.find_parent(['div', 'article', 'li'])
            if not card:
                continue
                
            text = card.text.strip()
            
            # Find the title link inside this card
            # Usually the largest text link or a heading link inside the card
            links = card.find_all('a')
            event_link = None
            title = None
            
            for l in links:
                l_text = l.text.strip()
                # Skip the "Share Event" link itself
                if "Share Event" in l_text or not l_text:
                    continue
                # The first valid link text we find is almost always the event name
                title = l_text
                event_link = l['href']
                break
                
            # Fallback if no specific title link was isolated
            if not title:
                heading = card.find(['h2', 'h3', 'h4', 'p'])
                if heading:
                    title = heading.text.strip()
            
            # Clean up title fragments or navigation leakage
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
        print(f"Successfully generated salsa_feed.xml with {events_count} unique events!")
    else:
        print("Warning: No events found using the 'Share Event' structural anchor.")

if __name__ == "__main__":
    scrape_and_create_feed()
