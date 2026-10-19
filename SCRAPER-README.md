# MyGab TV companion scraper

This companion script adapts the Selenium/BeautifulSoup extraction approach from the referenced scraper into a configurable helper for MyGab TV. It exports **candidate video/player links** as JSON; it does not download videos.

## Requirements

- Python 3.10+
- Google Chrome or Chromium installed
- Internet access to the public pages you choose

Install dependencies:

```bash
python -m pip install -r requirements-scraper.txt
```

Selenium 4 can manage a compatible ChromeDriver automatically on supported systems. If your machine cannot download/manage a driver, install a matching ChromeDriver and configure Selenium for your setup.

## Configure

Edit these text files (one entry per line):

- `sources.txt`: domains you have checked are adults-only, e.g. `example-adult-domain.invalid` (replace with a real domain you trust)
- `urls.txt`: public page URLs on those approved domains
- `keywords.txt`: optional words to require in the candidate title or URL. Leave empty to keep all otherwise eligible candidates.

Do not add YouTube. Do not use this tool to bypass logins, paywalls, access controls, or a site's restrictions. It only scans pages you are allowed to access.

Run:

```bash
python mygab_scraper.py --urls urls.txt --sources sources.txt --keywords keywords.txt --output mygab-results.json
```

Then open MyGab TV, unlock Admin, choose the generated `mygab-results.json` under **Import results from the standalone scraper (JSON)**, and select **Import scraper results**. MyGab TV only accepts links on domains saved in its own Approved websites list. Duplicate, unapproved, YouTube, invalid, and flagged age-related results are rejected.

## Important limits

- This is a candidate extractor, not a universal scraper. Some sites render video URLs inside protected APIs, encrypted scripts, DRM players, or cross-origin frames; those may not be extractable.
- It does not guarantee that a site or every result is adult-only. Maintain an adults-only domain allowlist and manually review results before playback. The title/URL keyword filter is only a precaution.
- It does not download, rehost, or transcode video. Playback still depends on the original site's player and Fire Stick/browser compatibility.
