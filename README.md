# Enhanced Steam Account Checker

A powerful Python tool for validating Steam session tokens, checking account status, and generating comprehensive reports with JWT token validation support.

## Features

- ✅ **JWT Token Validation** - Validates Steam JWT tokens and checks expiration
- 🔍 **Multiple Token Formats** - Supports `username----JWT` and standard cookie formats
- 📊 **Comprehensive Reports** - Generates detailed HTML reports with statistics
- 🚫 **Ban Detection** - Checks VAC, Community, and Economy bans
- 👤 **Profile Information** - Fetches user profiles and account details
- 🔄 **Retry Logic** - Built-in retry mechanism for failed requests
- 📝 **Logging** - Detailed logging for debugging and monitoring
- ⚡ **Performance Optimized** - Connection pooling and efficient processing

## Installation

### Prerequisites

- Python 3.7 or higher
- Steam Web API Key ([Get one here](https://steamcommunity.com/dev/apikey))

### Quick Setup

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/ZoniBoy00/Steam-Account-Checker
   cd Steam-Account-Checker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your Steam API Key**
   
   Open `steam_checker.py` and replace `YOUR_STEAM_API_KEY` with your actual Steam Web API key:
   ```python
   STEAM_API_KEY = "your_actual_steam_api_key_here"
   ```

4. **Prepare your tokens file**
   
   Create a `tokens.json` file with your Steam tokens (see [Token Formats](#token-formats) below)

## Usage

### Simple Usage

```bash
python steam_checker.py
```

The script will automatically:
1. Validate your configuration and API key
2. Read tokens from `tokens.json`
3. Process each token with JWT validation
4. Check account status and ban information
5. Generate a detailed HTML report (`steam_account_report.html`)
6. Display comprehensive summary statistics

### Token Formats

The tool supports multiple token formats in your `tokens.json` file:

#### Format 1: Username----JWT Format (Recommended)
```json
[
  "curtain2181----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSIsInN1YiI6Ijc2NTYxMTk5MDI0OTU1NTY3IiwiYXVkIjpbImNsaWVudCIsIndlYiIsInJlbmV3IiwiZGVyaXZlIl0sImV4cCI6MTc1MjI2NDgyOCwibmJmIjoxNzI1NTQ5MzIwLCJpYXQiOjE3MzQxODkzMjAsImp0aSI6IjAwMDlfMjU4M0UyRThfODE2NDkiLCJvYXQiOjE3MzQxODkzMjAsInBlciI6MSwiaXBfc3ViamVjdCI6IjE4My4yNC4xNTUuMjIyIiwiaXBfY29uZmlybWVyIjoiMjIzLjEwNC43OC4xNTkifQ.lOcHgoEKfm1ryWtMvPNGJEn3TnPSIljtx6Kijuu-fCh9XvcHqADeg9w2F0eqqOgGbRSABMMmmkZwvsVsETuBw"
]
```

#### Format 2: Cookie Format
```json
[
  "steamLoginSecure=eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9...; sessionid=abc123"
]
```

#### Format 3: Direct JWT
```json
[
  "eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSIsInN1YiI6Ijc2NTYxMTk5MDI0OTU1NTY3In0.signature"
]
```

#### Format 4: Object Format
```json
{
  "tokens": [
    "token1",
    "token2"
  ]
}
```

### Configuration Options

You can modify these settings in `steam_checker.py`:

```python
STEAM_API_KEY = "YOUR_STEAM_API_KEY"      # Your Steam Web API key
INPUT_FILE = "tokens.json"                # Input file path
OUTPUT_FILE = "steam_account_report.html" # Output report path
DELAY_BETWEEN_REQUESTS = 2                # Delay between requests (seconds)
REQUEST_TIMEOUT = 10                      # Request timeout (seconds)
MAX_RETRIES = 3                           # Maximum retry attempts
```

## Output

### Console Output
The script provides real-time progress updates showing:
- Configuration validation results
- Token parsing and JWT validation status
- Steam ID extraction and verification
- Account validation and session testing
- Ban status checking (VAC, Community, Economy)
- Processing statistics and completion status

### HTML Report
A comprehensive HTML report is generated containing:
- **Summary Statistics** - Overview of all accounts processed
- **Detailed Account Table** - Individual account information including:
  - Account status (Valid/Invalid/Expired)
  - Steam ID and username
  - Ban status (VAC, Community, Economy)
  - Account creation and last online dates
  - JWT validation results
  - Token expiration dates

### Log File
Detailed logs are saved to `steam_checker.log` for debugging and monitoring.

## Understanding the Results

### Account Status
- **Valid** - Token is valid and account is accessible
- **Invalid** - Token is malformed or account is inaccessible  
- **Expired** - JWT token has expired
- **Session Invalid** - Token format is valid but session is not active
- **Error** - An error occurred during processing

### JWT Validation
- **JWT Valid: Yes** - Token structure is valid and not expired
- **JWT Valid: No** - Token is invalid or expired
- **JWT Valid: N/A** - Token is not in JWT format

### Ban Status
- **VAC Banned** - Valve Anti-Cheat ban status
- **Community Banned** - Steam Community ban status
- **Economy Banned** - Steam Market/Trading ban status

## Troubleshooting

### Common Issues

1. **"Please set your Steam API key"**
   - Solution: Replace `YOUR_STEAM_API_KEY` with your actual Steam Web API key

2. **"No tokens found in tokens.json"**
   - Solution: Ensure `tokens.json` exists and contains valid token data

3. **"HTTP 429" or rate limiting errors**
   - Solution: Increase `DELAY_BETWEEN_REQUESTS` value

4. **"JWT parsing error"**
   - Solution: Verify token format is correct (should have 3 parts separated by dots)

5. **"Requirements check failed"**
   - Solution: Ensure Python 3.7+, valid tokens.json, and configured API key

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Review the `steam_checker.log` file for detailed error information
3. Verify your Steam API key is valid and active
4. Ensure your tokens are in the correct format

## Security Notes

- Keep your Steam API key secure and never share it publicly
- The tool only reads token information and doesn't modify accounts
- All network requests use HTTPS for security
- Tokens are processed locally and not sent to external services

## Performance Tips

- For large token lists, consider processing in smaller batches
- Adjust `DELAY_BETWEEN_REQUESTS` based on your needs (lower = faster, higher = more stable)
- The tool uses connection pooling for improved performance
- Enable logging level adjustment for better performance monitoring

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and legitimate account management purposes only. Users are responsible for complying with [Steam's Web API Terms of Use](https://steamcommunity.com/dev/apiterms) and applicable laws. The developers are not responsible for any misuse of this tool.
