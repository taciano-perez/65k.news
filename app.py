import requests
import feedparser
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from urllib.parse import quote
from time import mktime
from datetime import datetime

app = Flask(__name__)

RSS_FEEDS = [
    {"name": "Vox", "url": "https://www.vox.com/rss/index.xml"},
    {"name": "VoxLife", "url": "https://www.vox.com/rss/life/index.xml"},
    {"name": "TheConversation/Europe", "url": "https://theconversation.com/europe/home-page.atom"},
    {"name": "TheConversation/US", "url": "https://theconversation.com/us/articles.atom"}
]

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted tags completely
    # Added form, input, button
    for tag in soup(['script', 'style', 'img', 'video', 'iframe', 'svg', 'noscript', 'link', 'meta', 'figure', 'figcaption', 'form', 'input', 'button']):
        tag.decompose()
        
    # Find the main content container
    # Since we are now parsing the RSS 'content' field, it might not have <main> or specific classes.
    # It usually is just a bunch of <p> tags and headings.
    # So we should process the whole soup.
    
    # Unwrap divs, spans, AND anchors (keep text, remove tag)
    for tag in soup.find_all(['div', 'span', 'a']):
        tag.unwrap()

    # Simplify attributes for ALL remaining tags
    for tag in soup.find_all(True):
        tag.attrs = {} # Remove all attributes
        
    # Since we aren't looking for a container anymore (RSS content is the container),
    # just return the body contents or the soup itself if no body.
    # BeautifulSoup adds <html><body> if it parses a fragment? usually yes if using html.parser
    # But let's be safe.
    
    if soup.body:
        content = soup.body.decode_contents()
    else:
        content = str(soup)
    
    # Normalize curly quotes and replace non-breaking spaces
    content = content.replace('&nbsp;', ' ').replace('\xa0', ' ')
    content = content.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # Escape double quotes as requested
    return content.replace('"', '&quot;')

@app.route("/")
def index():
    try:
        # Parse disabled feeds
        disabled_arg = request.args.get('disabled', '')
        disabled_indices = set()
        if disabled_arg:
            try:
                disabled_indices = set(int(x) for x in disabled_arg.split(',') if x.strip().isdigit())
            except ValueError:
                pass # Ignore malformed input

        # Prepare feed toggles
        feed_toggles = []
        for i, feed in enumerate(RSS_FEEDS):
            is_enabled = i not in disabled_indices
            
            # Calculate new disabled set for the link
            new_disabled = disabled_indices.copy()
            if is_enabled:
                new_disabled.add(i)
            else:
                new_disabled.discard(i)
            
            # Generate URL
            if new_disabled:
                query_string = ",".join(map(str, sorted(new_disabled)))
                url = f"/?disabled={query_string}"
            else:
                url = "/"
                
            feed_toggles.append({
                "name": feed['name'],
                "enabled": is_enabled,
                "url": url
            })

        articles = []
        for feed_idx, feed_config in enumerate(RSS_FEEDS):
            if feed_idx in disabled_indices:
                continue

            try:
                feed = feedparser.parse(feed_config['url'])
                
                # Check for parsing errors if needed, but feedparser usually returns what it can.
                
                for entry_idx, entry in enumerate(feed.entries):
                    published_iso = ""
                    published_ts = 0
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_ts = mktime(entry.published_parsed)
                        dt = datetime.fromtimestamp(published_ts)
                        published_iso = dt.isoformat()
                    elif hasattr(entry, 'published'):
                         published_iso = entry.published
                    
                    if not published_iso:
                        published_iso = "Unknown Date"

                    articles.append({
                        "title": f"[{feed_config['name']}] {entry.title}",
                        "url": entry.link,
                        "published_at": entry.get('published', 'Unknown'),
                        "published_iso": published_iso,
                        "published_ts": published_ts,
                        "proxy_url": f"/article?id={feed_idx}-{entry_idx}"
                    })
            except Exception as e:
                # Log error and continue with other feeds
                print(f"Error fetching feed {feed_config['name']}: {e}")
                continue

        # Sort articles from latest to oldest
        articles.sort(key=lambda x: x['published_ts'], reverse=True)

        return render_template("index.html", articles=articles, feed_toggles=feed_toggles)
        
    except Exception as e:
        return render_template("error.html", message=f"Error fetching feeds: {e}"), 502

@app.route("/article")
def article():
    article_id = request.args.get("id")
    if not article_id:
        return render_template("error.html", message="No article ID provided."), 400

    try:
        if '-' not in article_id:
             return render_template("error.html", message="Invalid article ID format."), 400
             
        feed_idx_str, entry_idx_str = article_id.split('-')
        feed_idx = int(feed_idx_str)
        entry_idx = int(entry_idx_str)
    except ValueError:
        return render_template("error.html", message="Invalid article ID values."), 400

    try:
        if feed_idx < 0 or feed_idx >= len(RSS_FEEDS):
             return render_template("error.html", message="Feed not found."), 404
             
        feed_config = RSS_FEEDS[feed_idx]
        # Re-fetch the specific feed
        feed = feedparser.parse(feed_config['url'])
        
        if entry_idx < 0 or entry_idx >= len(feed.entries):
             return render_template("error.html", message="Article not found in feed."), 404
        
        target_entry = feed.entries[entry_idx]
        
        # Extract content
        raw_content = ""
        if 'content' in target_entry:
             for content_item in target_entry.content:
                 if content_item.type == 'text/html':
                     raw_content = content_item.value
                     break
        elif 'summary' in target_entry:
            raw_content = target_entry.summary
            
        if not raw_content:
            raw_content = "<p>No content available.</p>"

        cleaned_content = clean_html(raw_content)
        title = target_entry.title
        author = target_entry.get("author", "Unknown Author")
        
        return render_template("article.html", title=title, author=author, content=cleaned_content, original_url=target_entry.link)

    except Exception as e:
        return render_template("error.html", message=f"Error fetching article: {e}"), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
