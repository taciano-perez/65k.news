# 65k.news

A simplified news aggregator designed for vintage computers and text-based browsers. It fetches articles from the [Vox.com RSS feed](https://www.vox.com/rss/index.xml) and displays them in a strictly lightweight HTML format.

## Design Philosophy

*   **Simplicity:** No CSS, no JavaScript, no images, no colors.
*   **Compatibility:** Minimalist HTML designed to render correctly on browsers from the early 90s (Netscape 1.0, Mosaic, Lynx, etc.).
*   **Performance:** Extremely small payload, stripping all embellishments to focus purely on content.

## Features

*   Headline listing from Vox RSS.
*   Internal article proxy that strips all non-essential HTML tags.
*   Removes links, forms, images, and styling from article bodies.
*   Displays author bylines and clear navigation.

## Prerequisites

*   Python 3.6+

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/65k.news.git
    cd 65k.news
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the application:
    ```bash
    python app.py
    ```

2.  Open your browser and navigate to:
    ```
    http://localhost:5000
    ```
    (Or `http://<your-local-ip>:5000` to access from another device on your network).

## Running Tests

To run the automated test suite:
```bash
python -m unittest test_app.py
```

## Credits

*   Content provided by [Vox.com](https://www.vox.com)
*   Inspired by [68k.news](https://github.com/ActionRetro/68k-news) by ActionRetro
