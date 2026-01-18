# 65k.news

A simplified news aggregator designed for vintage computers and text-based browsers. It fetches top headlines from [thenewsapi.com](https://thenewsapi.com) and displays them in a lightweight HTML 4.01 format.

## Design Philosophy

*   **Simplicity:** No CSS, no JavaScript, no images (except external favicons if supported).
*   **Compatibility:** Valid HTML 4.01 Strict. Should render correctly on almost any browser from the 90s onwards (Netscape Navigator, Internet Explorer 3+, Mosaic, Lynx, etc.).
*   **Performance:** Extremely lightweight payload for slow connections.

## Prerequisites

*   Python 3.6+
*   An API key from [thenewsapi.com](https://thenewsapi.com) (Free tier available)

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

3.  Configure your API key:
    *   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        # or on Windows: copy .env.example .env
        ```
    *   Open `.env` and paste your API key:
        ```
        API_TOKEN=your_actual_api_token_here
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

*   Powered by [thenewsapi.com](https://thenewsapi.com)
*   Inspired by [68k.news](https://github.com/ActionRetro/68k-news) by ActionRetro