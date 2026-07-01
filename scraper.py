import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Target URL
URL = "https://www.salsavida.com/guides/new-york/new-york-city/socials/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Expanded list of structural words and phrases to ignore
NAVIGATION_BLACKLIST = {
    "home", "guides", "events", "news", "articles", "videos", "shop", 
    "add event", "contact", "about", "terms of service", "privacy policy",
    "north america", "salsa dance terms", "dance terms"
}

# Expanded list of exact URLs and partial paths to filter out
URL_BLACKLIST = {
    "https://www.salsavida.com/", 
    "https://www.salsavida.com/guides/",
    "https://www.salsavida.com/guides/north-america/", 
    "https://www.salsavida.com/salsa-dance-terms/",
    "/", 
    "/guides/", 
    "/events/", 
    "/news/", 
    "/articles/", 
    "/videos/", 
    "/shop/",
    "/guides/north-america/", 
    "/salsa-dance-terms/"
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
    share_buttons = soup.find_all(lambda tag: tag.name in ['a', 'div', 'button'] and tag.text and "Share Event" in tag.text)
    
    for btn in share_buttons:
        try:
            # Move up to the closest container box that holds this specific event's info
            card = btn.find_parent(['div', 'article', 'li'])
            if not card:
                continue
                
            text = card.text.strip()
            
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
                    
                # Skip static navigation links or main utility pages
                if l_text.lower() in NAVIGATION_BLACKLIST or l_href in URL_BLACKLIST:
                    continue
                    
                # The first valid link text that passes the filter is our event name
                title = l_text
                event_link = l_href
                break
                
            # Fallback if no specific title link was isolated
            if not title:
                heading = card.find(['h2', 'h3', 'h4', 'p'])
                if heading and heading.text.strip().lower() not in NAVIGATION_BLACKLIST:
                    title = heading.text.strip()
            
            # Final validation check on the title
            if not title or len(title) < 3 or title.lower() in NAVIGATION_BLACKLIST or title in seen_titles:
                continue
                
            # Clean up the link URL
            link = event_link if event_link else URL
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
            elif not link.startswith('http'):
                link = URL
                
            # Double check full finalized link against the blacklist
            if link in URL_BLACKLIST:
                continue
                
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
        print(f"Successfully generated salsa_feed.xml with {events_count} clean events!")
    else:
        print("Warning: No events found matching the criteria.")

if __name__ == "__main__":
    scrape_and_create_feed()
