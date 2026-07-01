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
    
    seen_titles = set()
    events_count = 0
    
    # Grab all standard container boxes on the page
    containers = soup.find_all(['div', 'article', 'li'])
    
    for card in containers:
        try:
            text = card.text.strip()
            
            # THE TITANIUM FILTER: Based directly on your screenshot
            has_time = re.search(r'\d{1,2}:\d{2}\s?[AaPp][Mm]', text)
            has_year = re.search(r'202\d', text)
            has_ny = "New York" in text
            
            # If the block doesn't have all three, it's a random link. Skip it instantly.
            if not (has_time and has_year and has_ny):
                continue
                
            # Filter out giant, invisible website wrappers (a real event card is short)
            if len(text) > 800:
                continue
            
            # Find the title link inside this specific card
            links = card.find_all('a')
            event_link = None
            title = None
            
            for l in links:
                l_text = l.text.strip()
                l_href = l.get('href', '')
                
                # Skip any empty links or raw icons
                if not l_text:
                    continue
                    
                title = l_text
                event_link = l_href
                break
                
            # Fallback if the title wasn't a direct link
            if not title:
                heading = card.find(['h2', 'h3', 'h4', 'strong'])
                if heading:
                    title = heading.text.strip()
            
            # Final validation to prevent duplicates
            if not title or len(title) < 3 or title in seen_titles:
                continue
                
            # Clean up the link URL
            link = event_link if event_link else URL
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
            elif not link.startswith('http'):
                link = URL
                
            # Clean up description text so it looks nice in your RSS reader
            desc = " ".join(text.split())
            
            # Extract the event thumbnail if available
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
            continue

    # Save the finished RSS feed
    if events_count > 0:
        fg.rss_file('salsa_feed.xml', pretty=True)
        print(f"Successfully generated salsa_feed.xml with {events_count} perfect events!")
    else:
        print("Warning: No events found matching the criteria.")

if __name__ == "__main__":
    scrape_and_create_feed()
