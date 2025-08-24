You're absolutely right! The format shown in the README is outdated and incorrect. Let me correct that section with the proper format based on the JWT token format we've been working with:

# Steam Account Validator & Ban Checker

A Python tool that validates Steam accounts using session cookies and checks for VAC, Community, and Economy bans. It fetches core profile details and generates a professional HTML report with everything in one place.

---

## Table of Contents

* [Features](#features)
* [Requirements](#requirements)
* [Installation](#installation)
* [Setup](#setup)
* [Configuration](#configuration)
* [Usage](#usage)
* [Output](#output)
* [Report Contents](#report-contents)
* [How It Works](#how-it-works)
* [Rate Limiting](#rate-limiting)
* [Error Handling](#error-handling)
* [Security & Privacy](#security--privacy)
* [Troubleshooting](#troubleshooting)
* [FAQ](#faq)
* [Contributors](#contributors)
* [License](#license)
* [Buy Me A Coffee](#buy-me-a-coffee)

---

## Features

* ✅ Validates Steam session cookies
* ✅ Checks **VAC**, **Community**, and **Economy** bans
* ✅ Retrieves profile info (username, real name, Steam64, etc.)
* ✅ Generates a **professional HTML report** with per-account details
* ✅ **Profile links** in HTML report for easy access to Steam profiles
* ✅ Built‑in **rate limiting** to avoid API throttling
* ✅ **Comprehensive error handling** and clear console status

---

## Requirements

* **Python**: 3.6+
* **Packages**: see `requirements.txt`

> Typical dependencies for this kind of tool include `requests` and `jinja2` (for HTML templating). Always rely on the provided `requirements.txt`.

---

## Installation

```bash
# Create/activate a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Setup

1. **Get a Steam Web API Key**

   * Visit: [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
   * Register your application to obtain a free API key.

2. **Create `tokens.json` with your Steam session cookies**
   File format:

   ```json
   [
     "curtain2181----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSIsInN1YiI6Ijc2NTYxMTk5MDI0OTU1NTY3IiwiYXVkIjpbImNsaWVudCIsIndlYiIsInJlbmV3IiwiZGVyaXZlIl0sImV4cCI6MTc1MjI2NDgyOCwibmJmIjoxNzI1NTQ5MzIwLCJpYXQiOjE3MzQxODkzMjAsImp0aSI6IjAwMDlfMjU4M0UyRThfODE2NDkiLCJvYXQiOjE3MzQxODkzMjAsInBlciI6MSwiaXBfc3ViamVjdCI6IjE4My4yNC4xNTUuMjIyIiwiaXBfY29uZmlybWVyIjoiMjIzLjEwNC43OC4xNTkifQ.lOcHgoEKfm1ryWtMvPNGJEn3TnPSIljtx6Kijuu-fCh9XvcHqADeg9w2F0eqqOgGbRSABMMmmkZwvsVsETuBw",
     "curtain2181----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSIsInN1YiI6Ijc2NTYxMTk5MDI0OTU1NTY3IiwiYXVkIjpbImNsaWVudCIsIndlYiIsInJlbmV3IiwiZGVyaXZlIl0sImV4cCI6MTc1MjI2NDgyOCwibmJmIjoxNzI1NTQ5MzIwLCJpYXQiOjE3MzQxODkzMjAsImp0aSI6IjAwMDlfMjU4M0UyRThfODE2NDkiLCJvYXQiOjE3MzQxODkzMjAsInBlciI6MSwiaXBfc3ViamVjdCI6IjE4My4yNC4xNTUuMjIyIiwiaXBfY29uZmlybWVyIjoiMjIzLjEwNC43OC4xNTkifQ.lOcHgoEKfm1ryWtMvPNGJEn3TnPSIljtx6Kijuu-fCh9XvcHqADeg9w2F0eqqOgGbRSABMMmmkZwvsVsETuBw"
   ]
   ```

   Or if using traditional cookie format:
   
   ```json
   [
     "steamLoginSecure=curtain2181----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSIsInN1YiI6Ijc2NTYxMTk5MDI0OTU1NTY3IiwiYXVkIjpbImNsaWVudCIsIndlYiIsInJlbmV3IiwiZGVyaXZlIl0sImV4cCI6MTc1MjI2NDgyOCwibmJmIjoxNzI1NTQ5MzIwLCJpYXQiOjE3MzQxODkzMjAsImp0aSI6IjAwMDlfMjU4M0UyRThfODE2NDkiLCJvYXQiOjE3MzQxODkzMjAsInBlciI6MSwiaXBfc3ViamVjdCI6IjE4My4yNC4xNTUuMjIyIiwiaXBfY29uZmlybWVyIjoiMjIzLjEwNC43OC4xNTkifQ.lOcHgoEKfm1ryWtMvPNGJEn3TnPSIljtx6Kijuu-fCh9XvcHqADeg9w2F0eqqOgGbRSABMMmmkZwvsVsETuBw",
     "steamLoginSecure=curtain2181----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSIsInN1YiI6Ijc2NTYxMTk5MDI0OTU1NTY3IiwiYXVkIjpbImNsaWVudCIsIndlYiIsInJlbmV3IiwiZGVyaXZlIl0sImV4cCI6MTc1MjI2NDgyOCwibmJmIjoxNzI1NTQ5MzIwLCJpYXQiOjE3MzQxODkzMjAsImp0aSI6IjAwMDlfMjU4M0UyRThfODE2NDkiLCJvYXQiOjE3MzQxODkzMjAsInBlciI6MSwiaXBfc3ViamVjdCI6IjE4My4yNC4xNTUuMjIyIiwiaXBfY29uZmlybWVyIjoiMjIzLjEwNC43OC4xNTkifQ.lOcHgoEKfm1ryWtMvPNGJEn3TnPSIljtx6Kijuu-fCh9XvcHqADeg9w2F0eqqOgGbRSABMMmmkZwvsVsETuBw"
   ]
   ```

3. **Set your API key in the script**
   Open `steam_checker.py` and update:

   ```python
   STEAM_API_KEY = "YOUR_API_KEY_HERE"
   ```

---

## Configuration

Edit the constants at the top of `steam_checker.py`:

* `STEAM_API_KEY`: Your Steam Web API key
* `INPUT_FILE`: Path to tokens file (default likely `tokens.json`)
* `OUTPUT_FILE`: Path to the HTML report (e.g., `steam_account_report.html`)
* `DELAY_BETWEEN_REQUESTS`: Delay in seconds between API calls

> Tip: If you prefer environment variables, you can adapt the script to read `STEAM_API_KEY` from `os.environ`—but by default it reads from the constant.

---

## Usage

Run the checker:

```bash
python steam_checker.py
```

You'll see live console status (validations, counts, and a final summary). When finished, open the generated report in your browser.

---

## Output

* **`steam_account_report.html`** — a polished, self-contained HTML report of all processed accounts
* **Console summary** — status per token plus totals

---

## Report Contents

For each account, the report includes:

* Account index / number
* Status: **Valid**, **Invalid**, or **Error**
* **Steam64 ID**
* **Username** and **Real name** (if available)
* Ban statuses: **VAC**, **Community**, **Economy**
* Ban counts and details (where available)
* Account **creation date**
* **Last online** time
* **Profile link** - direct link to Steam profile for quick access

---

## How It Works

1. **Cookie Validation** — Each cookie string is parsed and used to call Steam endpoints to confirm session validity.
2. **Profile Fetch** — The script retrieves core profile details (e.g., persona name, real name, Steam64).
3. **Ban Checks** — VAC, Community, and Economy ban statuses are queried via the Steam Web API.
4. **Profile Links** — Each account includes a direct link to the Steam profile for easy access.
5. **Rate Limiting** — Requests are spaced using `DELAY_BETWEEN_REQUESTS` to respect Steam's limits.
6. **Report Generation** — Results are collated into a clean, professional HTML report.

---

## Rate Limiting

* Steam Web API typically enforces **~100 requests/hour** per key.
* The script automatically delays between calls using `DELAY_BETWEEN_REQUESTS`.
* If you process many tokens, consider increasing the delay to reduce throttling risk.

---

## Error Handling

The script aims to **fail gracefully** and continue processing other accounts:

* Invalid/expired cookies → marked **Invalid** with reason
* API/network errors → marked **Error** with details in console
* Missing fields → handled with defaults in the report

---

## Security & Privacy

* All data is processed **locally**.
* Keep your `tokens.json` and API key **private**—do not commit them to version control.
* Rotate session cookies and API keys if you suspect exposure.
* Consider using a dedicated, limited-scope environment when running the tool.

---

## Troubleshooting

* **Invalid cookies**

  * Confirm `tokens.json` strings match the required format (either JWT format starting with "curtain2181----" or traditional cookie format).
* **API key issues**

  * Double-check `STEAM_API_KEY` in `steam_checker.py` and that your key is active.
* **Rate limit / Too many requests**

  * Increase `DELAY_BETWEEN_REQUESTS` and retry later.
* **No report generated**

  * Check console for exceptions; ensure `OUTPUT_FILE` path is writable.
* **Network errors**

  * Verify internet connectivity and that Steam APIs aren't temporarily unavailable.

---

## FAQ

**Q: Can I put more than five tokens in `tokens.json`?**
A: Yes. The shown file is an example—add as many as you need (keeping rate limits in mind).

**Q: Do I have to use cookies?**
A: Yes. This tool validates sessions via cookies and complements that with Web API checks.

**Q: Can I change the report's look?**
A: Absolutely—modify the HTML template/CSS section inside `template.py`.

**Q: What's the new Profile link feature?**
A: Each account in the HTML report now includes a "View" link that opens the Steam profile directly in a new tab.

---

## Contributors

* ZoniBoy00 (@ZoniBoy00)

> Want to contribute? Open an issue or PR with proposed changes. Please avoid submitting secrets or real tokens in examples.

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/ZoniBoy00/Steam-Account-Checker/blob/main/LICENSE) file for details.

---

## Buy Me A Coffee
[Donate](https://buymeacoffee.com/zoniboy00)

---

## At a Glance (Copy/Paste Quickstart)

```bash
# 1) Install
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2) Configure
# - Get API key: https://steamcommunity.com/dev/apikey  
# - Put cookies in tokens.json (see README)
# - Edit STEAM_API_KEY and paths in steam_checker.py

# 3) Run
python steam_checker.py

# 4) Open the report
open steam_account_report.html  # macOS
xdg-open steam_account_report.html  # Linux
start steam_account_report.html  # Windows
```