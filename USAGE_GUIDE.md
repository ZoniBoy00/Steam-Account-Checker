# Steam Account Checker - Complete Usage Guide

## Quick Start

1. **Install Python 3.7+** and dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Steam API Key** from [Steam Web API](https://steamcommunity.com/dev/apikey)

3. **Configure the script**:
   - Open `steam_checker.py`
   - Replace `YOUR_STEAM_API_KEY` with your actual API key

4. **Prepare your tokens** in `tokens.json` (see examples below)

5. **Run the checker**:
   ```bash
   python steam_checker.py
   ```

## Token Format Examples

### Format 1: Username----JWT (Recommended)
```json
{
  "tokens": [
    "username123----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9...",
    "player456----eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9..."
  ]
}
```

### Format 2: Cookie String
```json
{
  "tokens": [
    "steamLoginSecure=eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9...; sessionid=abc123",
    "steamLoginSecure=eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9...; steamMachineAuth=def456"
  ]
}
```

### Format 3: Direct JWT Token
```json
{
  "tokens": [
    "eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSI...",
    "eyJhbGciOiJFRFJTQSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdGVhbSI..."
  ]
}
```

### Format 4: Simple Array
```json
[
  "token1_here",
  "token2_here",
  "token3_here"
]
```

## Configuration Options

Edit these variables in `steam_checker.py`:

```python
# Required - Get from https://steamcommunity.com/dev/apikey
STEAM_API_KEY = "YOUR_STEAM_API_KEY"

# File paths
INPUT_FILE = "tokens.json"
OUTPUT_FILE = "steam_account_report.html"

# Performance settings
DELAY_BETWEEN_REQUESTS = 2    # Seconds between API calls
REQUEST_TIMEOUT = 10          # Request timeout
MAX_RETRIES = 3              # Retry attempts for failed requests
```

## Understanding Results

### Account Status Types
- **Valid**: Token works, account accessible
- **Invalid**: Token malformed or account inaccessible  
- **Expired**: JWT token has expired
- **Session Invalid**: Token format valid but session inactive
- **Error**: Processing error occurred

### JWT Validation
- **JWT Valid: Yes**: Token structure valid and not expired
- **JWT Valid: No**: Token invalid or expired
- **JWT Valid: N/A**: Not a JWT format token

### Ban Status
- **VAC Banned**: Valve Anti-Cheat ban
- **Community Banned**: Steam Community restrictions
- **Economy Banned**: Market/Trading restrictions

## Output Files

### HTML Report (`steam_account_report.html`)
- Interactive table with all account details
- Summary statistics dashboard
- Sortable columns and responsive design
- Professional styling for easy viewing

### Log File (`steam_checker.log`)
- Detailed processing logs
- Error messages and debugging info
- Timestamps for all operations

### Console Output
- Real-time progress updates
- Token parsing results
- Validation status for each account

## Performance Tips

### For Large Token Lists
- Increase `DELAY_BETWEEN_REQUESTS` to avoid rate limiting
- Process in smaller batches if needed
- Monitor the log file for errors

### Optimization Settings
```python
# Conservative (stable)
DELAY_BETWEEN_REQUESTS = 3
MAX_RETRIES = 5

# Balanced (recommended)
DELAY_BETWEEN_REQUESTS = 2
MAX_RETRIES = 3

# Aggressive (fast but risky)
DELAY_BETWEEN_REQUESTS = 1
MAX_RETRIES = 2
```

## Troubleshooting

### Common Issues

**"Please set your Steam API key"**
- Solution: Replace `YOUR_STEAM_API_KEY` in `steam_checker.py`

**"No tokens found in tokens.json"**
- Check file exists and contains valid JSON
- Verify token format matches examples above

**"HTTP 429" Rate Limiting**
- Increase `DELAY_BETWEEN_REQUESTS` value
- Steam API has rate limits, be patient

**"JWT parsing error"**
- Ensure JWT tokens have 3 parts (header.payload.signature)
- Check for URL encoding issues

**Connection timeouts**
- Increase `REQUEST_TIMEOUT` value
- Check internet connection stability

### Debug Mode
Enable detailed logging by changing log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Best Practices

1. **Protect your API key** - Never share or commit to version control
2. **Secure token storage** - Keep tokens.json private and secure
3. **Network security** - Use HTTPS connections only
4. **Local processing** - Tokens are processed locally, not sent externally

## Advanced Usage

### Custom Token Sources
Modify `read_tokens_from_json()` to read from:
- CSV files
- Databases
- API endpoints
- Text files

### Batch Processing
```python
# Process tokens in batches of 50
batch_size = 50
for i in range(0, len(tokens), batch_size):
    batch = tokens[i:i+batch_size]
    process_batch(batch)
```

### Custom Output Formats
Extend the script to export:
- CSV reports
- JSON data
- Database records
- API responses

## API Rate Limits

Steam Web API limits:
- **100,000 calls per day** per API key
- **1 call per second** recommended
- **Burst limits** may apply

Monitor your usage and adjust delays accordingly.

## Legal Compliance

- Use only for legitimate account management
- Respect Steam's Terms of Service
- Don't use for unauthorized access
- Comply with applicable laws and regulations

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Verify configuration settings
4. Test with a small token sample first
