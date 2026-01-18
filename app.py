import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_TOKEN = os.getenv("API_TOKEN")
BASE_URL = "https://api.thenewsapi.com/v1/news/all"

@app.route("/")
def index():
    if not API_TOKEN:
        return render_template("error.html", message="API_TOKEN is missing. Please check your .env file."), 500

    # Get optional filters from query parameters
    # e.g. /?cat=tech or /?q=bitcoin
    category = request.args.get("cat")
    search_query = request.args.get("q")
    
    params = {
        "api_token": API_TOKEN,
        "language": "en",
        "limit": 10
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    if category:
        params["categories"] = category
    if search_query:
        params["search"] = search_query

    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get("data", [])
        return render_template("index.html", articles=articles)
        
    except requests.exceptions.RequestException as e:
        return render_template("error.html", message=f"Error fetching news: {e}"), 502
    except ValueError:
        return render_template("error.html", message="Error parsing news data."), 500

if __name__ == "__main__":
    # Host on 0.0.0.0 to be accessible on local network (useful for testing on old machines)
    # Port 80 would be ideal for true retro, but requires admin. 5000 is default.
    app.run(host="0.0.0.0", port=5000)
