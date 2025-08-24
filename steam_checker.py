import requests
import csv
import time
import re
import urllib.parse
import base64
import json
from datetime import datetime

# ==================== CONFIGURATION ====================
STEAM_API_KEY = "YOUR_STEAM_API_KEY"  # Replace with your actual Steam Web API key
INPUT_FILE = "tokens.json"            # File containing Steam session cookies in JSON format
OUTPUT_FILE = "steam_account_report.html"
DELAY_BETWEEN_REQUESTS = 3            # Seconds between requests
# =======================================================

# ==================== HEADERS ====================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
# =======================================================


class SteamSessionManager:
    """Handles Steam API interactions and session management"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def parse_cookies_from_line(self, cookie_line):
        """Parse cookie line into dictionary"""
        cookies = {}
        if not cookie_line:
            return cookies
            
        # Split by semicolon and then by equals
        parts = cookie_line.strip().split(';')
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
        return cookies
    
    def extract_steamid_from_jwt(self, jwt_string):
        """Extract Steam64 ID from JWT token"""
        try:
            # Handle URL encoding
            if '%' in jwt_string:
                jwt_string = urllib.parse.unquote(jwt_string)
            
            # Check if it's in the format we expect (like: "76561198995224220||...")
            if '||' in jwt_string:
                parts = jwt_string.split('||')
                if len(parts) >= 2:
                    steam_id = parts[0]
                    if steam_id.isdigit() and len(steam_id) == 17:
                        return steam_id
            
            # Try to decode JWT payload
            if '.' in jwt_string:
                # Split into parts
                parts = jwt_string.split('.')
                if len(parts) >= 2:
                    payload_part = parts[1]
                    # Add padding if needed
                    payload_part += '=' * (4 - len(payload_part) % 4)
                    try:
                        payload_bytes = base64.urlsafe_b64decode(payload_part)
                        payload_json = payload_bytes.decode('utf-8')
                        
                        # Parse JSON to find steamid
                        if '"sub"' in payload_json:
                            match = re.search(r'"sub"\s*:\s*"(\d{17})"', payload_json)
                            if match:
                                return match.group(1)
                                
                        # Alternative: look for steamid in different formats
                        match = re.search(r'"steamid"\s*:\s*"(\d{17})"', payload_json)
                        if match:
                            return match.group(1)
                            
                    except:
                        pass
                        
        except Exception:
            pass
            
        return None
    
    def extract_steamid_from_cookies(self, cookies_dict):
        """Extract Steam64 ID from cookies"""
        steam_login_secure = cookies_dict.get('steamLoginSecure', '')
        
        if not steam_login_secure:
            return None
            
        # First, try to extract from the JWT format
        steam_id = self.extract_steamid_from_jwt(steam_login_secure)
        
        # If that fails, try URL decoding and pattern matching
        if not steam_id:
            try:
                # URL decode the cookie value
                decoded_value = urllib.parse.unquote(steam_login_secure)
                
                # Look for Steam64 ID pattern (17 digits)
                steam_id_match = re.search(r'(\d{17})', decoded_value)
                if steam_id_match:
                    steam_id = steam_id_match.group(1)
            except:
                pass
                
        # If we still don't have a valid Steam64 ID, return None
        if steam_id and steam_id.isdigit() and len(steam_id) == 17:
            return steam_id
        else:
            return None
    
    def validate_session_with_cookies(self, cookies_dict):
        """Validate session by making a request to Steam"""
        try:
            # Clear existing cookies
            self.session.cookies.clear()
            
            # Set new cookies
            for key, value in cookies_dict.items():
                self.session.cookies.set(key, value)
            
            # Test if session is valid by requesting a Steam page
            test_url = "https://store.steampowered.com/account/"
            
            response = self.session.get(test_url, timeout=10)
            
            # Check if we're logged in
            is_logged_in = (
                'logout' in response.text.lower() or 
                'account settings' in response.text.lower() or
                'welcome' in response.text.lower() or
                'profile' in response.text.lower() or
                'dashboard' in response.text.lower()
            )
            
            # Also check if we get proper content
            if response.status_code == 200 and len(response.text) > 1000:
                return {
                    "is_valid": is_logged_in,
                    "status_code": response.status_code,
                    "response_length": len(response.text),
                    "error": None
                }
            else:
                return {
                    "is_valid": False,
                    "status_code": response.status_code,
                    "response_length": len(response.text),
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "is_valid": False,
                "status_code": 0,
                "response_length": 0,
                "error": str(e)
            }
    
    def get_user_profile(self, steam_id):
        """Get user profile information using Steam Web API"""
        try:
            # Steam Web API endpoint for player summaries
            url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
            params = {
                "key": STEAM_API_KEY,
                "steamids": steam_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
                player = data["response"]["players"][0]
                return {
                    "username": player.get("personaname", "Unknown"),
                    "real_name": player.get("realname", "Not specified"),
                    "avatar": player.get("avatar", ""),
                    "profile_url": player.get("profileurl", ""),
                    "time_created": player.get("timecreated", 0),
                    "last_logoff": player.get("lastlogoff", 0),
                    "persona_state": player.get("personastate", 0)
                }
            else:
                return {
                    "username": "Unknown",
                    "real_name": "Not specified",
                    "avatar": "",
                    "profile_url": "",
                    "time_created": 0,
                    "last_logoff": 0,
                    "persona_state": 0
                }
                
        except Exception as e:
            return {
                "username": "Error",
                "real_name": "Error",
                "avatar": "",
                "profile_url": "",
                "time_created": 0,
                "last_logoff": 0,
                "persona_state": 0
            }
    
    def check_bans_for_steamid(self, steam_id):
        """Check bans for a given Steam64 ID using Steam Web API"""
        if not steam_id or len(steam_id) != 17 or not steam_id.isdigit():
            return {
                "VACBanned": False,
                "CommunityBanned": False,
                "EconomyBan": "invalid_id",
                "NumberOfVACBans": 0,
                "DaysSinceLastBan": 0,
                "NumberOfGameBans": 0,
                "SteamID": ""
            }
        
        try:
            # Steam Web API endpoint for player bans
            url = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
            params = {
                "key": STEAM_API_KEY,
                "steamids": steam_id
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "players" in data and len(data["players"]) > 0:
                player = data["players"][0]
                return {
                    "VACBanned": bool(player.get("VACBanned", False)),
                    "CommunityBanned": bool(player.get("CommunityBanned", False)),
                    "EconomyBan": player.get("EconomyBan", "none"),
                    "NumberOfVACBans": player.get("NumberOfVACBans", 0),
                    "DaysSinceLastBan": player.get("DaysSinceLastBan", 0),
                    "NumberOfGameBans": player.get("NumberOfGameBans", 0),
                    "SteamID": player.get("SteamId", "")
                }
            else:
                return {
                    "VACBanned": False,
                    "CommunityBanned": False,
                    "EconomyBan": "no_data",
                    "NumberOfVACBans": 0,
                    "DaysSinceLastBan": 0,
                    "NumberOfGameBans": 0,
                    "SteamID": ""
                }
                
        except Exception as e:
            return {
                "VACBanned": False,
                "CommunityBanned": False,
                "EconomyBan": "error",
                "NumberOfVACBans": 0,
                "DaysSinceLastBan": 0,
                "NumberOfGameBans": 0,
                "SteamID": ""
            }


def read_tokens_from_json(file_path):
    """Read tokens from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Direct array of token strings
            tokens = [token.strip() for token in data if token.strip()]
        elif isinstance(data, dict):
            # Dictionary with tokens under a key
            if 'tokens' in data:
                tokens = [token.strip() for token in data['tokens'] if token.strip()]
            else:
                # Try to find any array in the dict
                tokens = []
                for key, value in data.items():
                    if isinstance(value, list):
                        tokens.extend([item.strip() for item in value if item.strip()])
                        break
                if not tokens:
                    # If no array found, try to convert single token to list
                    if 'token' in data:
                        tokens = [data['token'].strip()] if data['token'].strip() else []
                    else:
                        tokens = []
        else:
            # Single string or other format
            tokens = [data.strip()] if data.strip() else []
        
        print(f"Found {len(tokens)} tokens in JSON file")
        return tokens
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return []


def format_timestamp(timestamp):
    """Convert Unix timestamp to readable date"""
    if timestamp and timestamp > 0:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "Never"


def format_ban_status(banned):
    """Format ban status for display"""
    return "Yes" if banned else "No"


def generate_html_report(accounts, file_path):
    """Generate HTML report with professional styling"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steam Account Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1b2836;
            text-align: center;
            border-bottom: 2px solid #1b2836;
            padding-bottom: 10px;
        }
        .summary {
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .summary h2 {
            margin-top: 0;
            color: #1b2836;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .summary-item {
            background-color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .summary-value {
            font-size: 24px;
            font-weight: bold;
            color: #1b2836;
        }
        .summary-label {
            font-size: 14px;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #1b2836;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #e8f4f8;
        }
        .status-valid {
            color: #28a745;
            font-weight: bold;
        }
        .status-invalid {
            color: #dc3545;
            font-weight: bold;
        }
        .status-error {
            color: #ffc107;
            font-weight: bold;
        }
        .ban-yes {
            color: #dc3545;
            font-weight: bold;
        }
        .ban-no {
            color: #28a745;
        }
        .account-number {
            font-weight: bold;
            color: #1b2836;
        }
        .header-section {
            text-align: center;
            margin-bottom: 30px;
        }
        .header-section p {
            color: #666;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <h1>Steam Account Validation Report</h1>
            <p>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
            <p>Report contains information about Steam accounts and their ban status</p>
        </div>
        
        <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">""" + str(len(accounts)) + """</div>
                    <div class="summary-label">Total Accounts</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">""" + str(sum(1 for a in accounts if a["Status"] == "Valid")) + """</div>
                    <div class="summary-label">Valid Accounts</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">""" + str(sum(1 for a in accounts if a["Status"] == "Invalid")) + """</div>
                    <div class="summary-label">Invalid Accounts</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">""" + str(sum(1 for a in accounts if a["VAC_Banned"] == "Yes")) + """</div>
                    <div class="summary-label">VAC Banned</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">""" + str(sum(1 for a in accounts if a["Community_Banned"] == "Yes")) + """</div>
                    <div class="summary-label">Community Banned</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">""" + str(sum(1 for a in accounts if a["Economy_Banned"] != "none" and a["Economy_Banned"] != "no_data" and a["Economy_Banned"] != "error")) + """</div>
                    <div class="summary-label">Economy Banned</div>
                </div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Account #</th>
                    <th>Status</th>
                    <th>Steam ID</th>
                    <th>Username</th>
                    <th>Real Name</th>
                    <th>VAC</th>
                    <th>Community</th>
                    <th>Economy</th>
                    <th>Ban Count</th>
                    <th>Created</th>
                    <th>Last Online</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for account in accounts:
        # Determine status class
        status_class = ""
        if account["Status"] == "Valid":
            status_class = "status-valid"
        elif account["Status"] == "Invalid":
            status_class = "status-invalid"
        else:
            status_class = "status-error"
        
        # Determine ban classes
        vac_class = "ban-yes" if account["VAC_Banned"] == "Yes" else "ban-no"
        community_class = "ban-yes" if account["Community_Banned"] == "Yes" else "ban-no"
        economy_class = "ban-yes" if account["Economy_Banned"] != "none" and account["Economy_Banned"] != "no_data" and account["Economy_Banned"] != "error" else "ban-no"
        
        html_content += f"""
                <tr>
                    <td class="account-number">{account['Account_Number']}</td>
                    <td class="{status_class}">{account['Status']}</td>
                    <td>{account['SteamID']}</td>
                    <td>{account['Username']}</td>
                    <td>{account['Real_Name']}</td>
                    <td class="{vac_class}">{account['VAC_Banned']}</td>
                    <td class="{community_class}">{account['Community_Banned']}</td>
                    <td class="{economy_class}">{account['Economy_Banned']}</td>
                    <td>{account['VAC_Count']}</td>
                    <td>{account['Account_Created']}</td>
                    <td>{account['Last_Online']}</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
    """
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML report saved to {file_path}")


def process_accounts(tokens):
    """Process all Steam accounts and return account data"""
    session_manager = SteamSessionManager()
    accounts = []
    
    # Process each token
    for i, token in enumerate(tokens, 1):
        print(f"\nProcessing Account #{i} of {len(tokens)}")
        print("-" * 40)
        print(f"Raw Token: {token[:80]}{'...' if len(token) > 80 else ''}")
        
        try:
            # Parse cookies from the line
            cookies = session_manager.parse_cookies_from_line(token)
            
            # Extract Steam64 ID
            steam_id = session_manager.extract_steamid_from_cookies(cookies)
            
            if steam_id:
                print(f"Steam ID: {steam_id}")
            else:
                print("No Steam ID found in token")
            
            # Validate session
            session_result = session_manager.validate_session_with_cookies(cookies)
            
            # Initialize default values
            user_profile = {
                "username": "Unknown",
                "real_name": "Not specified",
                "avatar": "",
                "profile_url": "",
                "time_created": 0,
                "last_logoff": 0,
                "persona_state": 0
            }
            
            ban_info = {
                "VACBanned": False,
                "CommunityBanned": False,
                "EconomyBan": "no_steamid",
                "NumberOfVACBans": 0,
                "DaysSinceLastBan": 0,
                "NumberOfGameBans": 0,
                "SteamID": ""
            }
            
            # Get ban status and profile if we have a valid Steam ID
            if steam_id:
                print("Checking ban status...")
                ban_info = session_manager.check_bans_for_steamid(steam_id)
                
                print("Fetching user profile...")
                user_profile = session_manager.get_user_profile(steam_id)
            else:
                print("Skipping ban and profile checks due to missing Steam ID")
            
            # Determine account status
            status = "Valid" if session_result["is_valid"] else "Invalid"
            
            # Create account record with enhanced data
            account = {
                "Account_Number": i,
                "Status": status,
                "SteamID": steam_id if steam_id else "Unknown",
                "Username": user_profile["username"],
                "Real_Name": user_profile["real_name"],
                "Profile_URL": user_profile["profile_url"],
                "VAC_Banned": format_ban_status(ban_info["VACBanned"]),
                "Community_Banned": format_ban_status(ban_info["CommunityBanned"]),
                "Economy_Banned": ban_info["EconomyBan"],
                "VAC_Count": ban_info["NumberOfVACBans"],
                "Days_Since_Last_Ban": ban_info["DaysSinceLastBan"],
                "Game_Bans": ban_info["NumberOfGameBans"],
                "Account_Created": format_timestamp(user_profile["time_created"]),
                "Last_Online": format_timestamp(user_profile["last_logoff"]),
                "Persona_State": user_profile["persona_state"]
            }
            
            accounts.append(account)
            
            # Display results
            print(f"Status: {status}")
            if steam_id:
                print(f"Username: {user_profile['username']}")
                print(f"VAC Banned: {format_ban_status(ban_info['VACBanned'])}")
                print(f"Community Banned: {format_ban_status(ban_info['CommunityBanned'])}")
                print(f"Economy Banned: {ban_info['EconomyBan']}")
            
            if session_result["error"]:
                print(f"Validation Error: {session_result['error']}")
            
        except Exception as e:
            print(f"Error processing token: {e}")
            account = {
                "Account_Number": i,
                "Status": "Error",
                "SteamID": "Error",
                "Username": "Error",
                "Real_Name": "Error",
                "Profile_URL": "",
                "VAC_Banned": "Error",
                "Community_Banned": "Error",
                "Economy_Banned": "Error",
                "VAC_Count": 0,
                "Days_Since_Last_Ban": 0,
                "Game_Bans": 0,
                "Account_Created": "Error",
                "Last_Online": "Error",
                "Persona_State": 0
            }
            accounts.append(account)
        
        # Add delay to avoid rate limiting
        if i < len(tokens):
            print(f"Waiting {DELAY_BETWEEN_REQUESTS} seconds before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    return accounts


def calculate_statistics(accounts):
    """Calculate summary statistics"""
    total_accounts = len(accounts)
    valid_accounts = sum(1 for a in accounts if a["Status"] == "Valid")
    invalid_accounts = sum(1 for a in accounts if a["Status"] == "Invalid")
    vac_banned = sum(1 for a in accounts if a["VAC_Banned"] == "Yes")
    community_banned = sum(1 for a in accounts if a["Community_Banned"] == "Yes")
    economy_banned = sum(1 for a in accounts if a["Economy_Banned"] != "none" and a["Economy_Banned"] != "no_data" and a["Economy_Banned"] != "error" and a["Economy_Banned"] != "Error")
    
    return {
        "total": total_accounts,
        "valid": valid_accounts,
        "invalid": invalid_accounts,
        "vac_banned": vac_banned,
        "community_banned": community_banned,
        "economy_banned": economy_banned
    }


def display_summary(statistics):
    """Display summary statistics"""
    print("\n" + "=" * 60)
    print("FINAL RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Accounts Checked: {statistics['total']}")
    print(f"Valid Accounts: {statistics['valid']}")
    print(f"Invalid Accounts: {statistics['invalid']}")
    print(f"VAC Banned Accounts: {statistics['vac_banned']}")
    print(f"Community Banned Accounts: {statistics['community_banned']}")
    print(f"Economy Banned Accounts: {statistics['economy_banned']}")
    print("=" * 60)


def main():
    """Main execution function"""
    print("=" * 60)
    print("STEAM ACCOUNT VALIDATOR & BAN CHECKER")
    print("=" * 60)
    print(f"Using Steam API Key: {STEAM_API_KEY[:10]}... (hidden for security)")
    print(f"Input File: {INPUT_FILE}")
    print(f"Output File: {OUTPUT_FILE}")
    print("=" * 60)
    
    # Read tokens
    tokens = read_tokens_from_json(INPUT_FILE)
    
    if not tokens:
        print("No tokens found in tokens.json")
        return

    print(f"Processing {len(tokens)} Steam accounts...")
    
    # Process accounts
    accounts = process_accounts(tokens)
    
    # Calculate statistics
    statistics = calculate_statistics(accounts)
    
    # Display summary
    display_summary(statistics)
    
    # Generate HTML report
    generate_html_report(accounts, OUTPUT_FILE)
    
    # Print completion message
    print("\nProcessing complete!")
    print(f"HTML report saved to: {OUTPUT_FILE}")
    print("Open the HTML file in any web browser for easy viewing")


if __name__ == "__main__":
    main()