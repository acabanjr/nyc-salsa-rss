for btn in share_buttons:
        try:
            # Move up to the closest container box
            card = btn.find_parent(['div', 'article', 'li'])
            if not card:
                continue
                
            text = card.text.strip()
            
            # THE TITANIUM FILTER: Must have a Time AND a Year AND say New York
            # This instantly destroys global sidebar ads for festivals in other states
            has_time = re.search(r'\d{1,2}:\d{2}\s?[AaPp][Mm]', text)
            has_year = re.search(r'202\d', text)
            has_ny = "New York" in text
            
            if not (has_time and has_year and has_ny):
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
