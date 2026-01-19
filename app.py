import requests
import feedparser
from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from urllib.parse import quote
from time import mktime
from datetime import datetime

app = Flask(__name__)

RSS_FEED_URL = "https://www.vox.com/rss/index.xml"

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
        feed = feedparser.parse(RSS_FEED_URL)
        articles = []
        for entry in feed.entries:
            published_iso = entry.published
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime.fromtimestamp(mktime(entry.published_parsed))
                published_iso = dt.isoformat()

            articles.append({
                "title": entry.title,
                "url": entry.link,
                "published_at": entry.published,
                "published_iso": published_iso,
                "proxy_url": f"/article?url={quote(entry.link)}"
            })
        
        return render_template("index.html", articles=articles)
        
    except Exception as e:
        return render_template("error.html", message=f"Error fetching feed: {e}"), 502

@app.route("/article")
def article():
    article_url = request.args.get("url")
    if not article_url:
        return render_template("error.html", message="No URL provided."), 400

    try:
        # Re-fetch the feed to find the content
        # In a production app, we would cache this.
        feed = feedparser.parse(RSS_FEED_URL)
        
        target_entry = None
        for entry in feed.entries:
            if entry.link == article_url:
                target_entry = entry
                break
        
        if not target_entry:
             return render_template("error.html", message="Article not found in current feed."), 404
        
        # Extract content
        # Vox RSS 'content' is a list of dicts: [{'type': 'text/html', 'value': '...'}]
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
        
        return render_template("article.html", title=title, author=author, content=cleaned_content, original_url=article_url)

    except Exception as e:
        return render_template("error.html", message=f"Error fetching article: {e}"), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
