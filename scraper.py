import os
import requests
import re
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ics import Calendar, Event

# Target URL
URL = "https://www.salsavida.com/guides/new-york/new-york-city/socials/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

BADGE_TEXTS = {"social", "class & social", "classes", "share event", "party"}
NY_TZ = ZoneInfo("America/New_York")

def normalize(text):
    if not text: return ""
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def scrape_and_create_feed():
    print("Fetching page...")
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch page: {e}")
        return
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize RSS
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("NYC Salsa Socials - Salsa Vida")
    fg.author({'name': 'Salsa RSS Bot'})
    fg.link(href=URL, rel='alternate')
    fg.description("Automated RSS feed for upcoming Salsa Socials in New York City.")
    fg.language('en')

    # Initialize ICS Calendar
    cal = Calendar()
    
    seen_unique_keys = set()
    events_count = 0
    
    containers = soup.find_all(['div', 'article', 'li'])
    
    for card in containers:
        try:
            text = card.text.strip()
            
            has_time = re.search(r'\d{1,2}:\d{2}\s?[AaPp][Mm]', text)
            has_year = re.search(r'202\d', text)
            has_ny = "New York" in text
            
            if not (has_time and has_year and has_ny) or len(text) > 800:
                continue
            
            # 1. FIND THE TITLE
            heading = card.find(['h2', 'h3', 'h4', 'h5', 'strong'])
            title = heading.text.strip() if heading else None
            
            if not title:
                for l in card.find_all('a'):
                    l_text = l.text.strip()
                    if l_text and l_text.lower() not in BADGE_TEXTS:
                        title = l_text
                        break
                        
            if not title or len(title) < 3 or title.lower() in BADGE_TEXTS:
                continue
                
            # 2. EXTRACT THE DATE & DEDUPLICATE
            date_match = re.search(r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s[A-Z][a-z]{2}\s\d{1,2},\s202\d', text)
            event_date = date_match.group(0) if date_match else "UnknownDate"
            
            unique_event_key = f"{normalize(title)}-{normalize(event_date)}"
            
            if unique_event_key in seen_unique_keys:
                continue
                
            seen_unique_keys.add(unique_event_key)
            
            # 3. EXTRACT THE LINK & DESCRIPTION
            event_link = None
            if heading and heading.find('a'):
                event_link = heading.find('a').get('href', '')
            else:
                for l in card.find_all('a'):
                    href = l.get('href', '')
                    txt = l.text.strip().lower()
                    if href and txt not in BADGE_TEXTS and "category" not in href and "salsavida.com" in href:
                        event_link = href
                        break
            
            link = event_link if event_link else URL
            if link.startswith('/'):
                link = "https://www.salsavida.com" + link
                
            desc = " ".join(text.split())
            img_element = card.find('img')
            img_url = img_element['src'] if img_element and img_element.has_attr('src') else None
            
            # --- CREATE RSS ITEM ---
            fe = fg.add_entry()
            fe.id(unique_event_key) 
            fe.title(f"{title} ({event_date})")
            fe.link(href=link)
            fe.description(desc)
            if img_url and img_url.startswith('http'):
                fe.enclosure(img_url, 0, 'image/jpeg')

            # --- CREATE ICS CALENDAR ITEM ---
            exact_date_match = re.search(r'([A-Z][a-z]{2}\s\d{1,2},\s202\d)', text)
            times = re.findall(r'\d{1,2}:\d{2}\s?[AaPp][Mm]', text)
            
            if exact_date_match and times:
                # Format string to look like "Jul 14 2026"
                clean_date = exact_date_match.group(1).replace(",", "").strip() 
                # Format time to look like "4:00PM"
                start_time_str = times[0].upper().replace(" ", "") 
                
                try:
                    start_dt = datetime.strptime(f"{clean_date} {start_time_str}", "%b %d %Y %I:%M%p").replace(tzinfo=NY_TZ)
                    end_dt = None
                    
                    if len(times) > 1:
                        end_time_str = times[1].upper().replace(" ", "")
                        end_dt = datetime.strptime(f"{clean_date} {end_time_str}", "%b %d %Y %I:%M%p").replace(tzinfo=NY_TZ)
                        # If end time is earlier than start time, it crossed midnight into the next day
                        if end_dt < start_dt:
                            end_dt += timedelta(days=1)
                    else:
                        # Default to 3 hours if no end time is specified
                        end_dt = start_dt + timedelta(hours=3)
                        
                    cal_event = Event()
                    cal_event.name = title
                    cal_event.begin = start_dt
                    cal_event.end = end_dt
                    cal_event.description = f"{desc}\n\nLink: {link}"
                    cal_event.url = link
                    cal.events.add(cal_event)
                except Exception as e:
                    print(f"Skipping calendar addition due to time parsing error for {title}: {e}")
                    pass
                
            events_count += 1
                
        except Exception as e:
            continue

    if events_count > 0:
        # Save XML file
        fg.rss_file('salsa_feed.xml', pretty=True)
        # Save ICS file
        with open('salsa_calendar.ics', 'w', encoding='utf-8') as f:
            f.writelines(cal.serialize_iter())
        print(f"Successfully generated salsa_feed.xml AND salsa_calendar.ics with {events_count} events!")
    else:
        print("Warning: No events found matching the criteria.")

if __name__ == "__main__":
    scrape_and_create_feed()
