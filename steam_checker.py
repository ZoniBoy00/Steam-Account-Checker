import requests
import csv
import time
import re
import urllib.parse
import base64
import json
from datetime import datetime

# ==================== IMPORT TEMPLATE FUNCTION ====================
# Import the render_report function from the template module
from template import render_report
# =======================================================

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

            # Try to decode JWT payload (the main fix!)
            if '.' in jwt_string:
                # Split into parts (header.payload.signature)
                parts = jwt_string.split('.')
                if len(parts) >= 2:
                    payload_part = parts[1]  # Payload is second part
                    
                    # Add padding if needed for base64 decoding
                    payload_part += '=' * (4 - len(payload_part) % 4)
                    
                    try:
                        # Decode base64 payload
                        payload_bytes = base64.urlsafe_b64decode(payload_part)
                        payload_str = payload_bytes.decode('utf-8')
                        
                        # Parse JSON to find steamid
                        payload_data = json.loads(payload_str)
                        
                        # Check for sub field (Steam ID) - this is where your JWT has it
                        steam_id = payload_data.get('sub')
                        if steam_id and str(steam_id).isdigit() and len(str(steam_id)) == 17:
                            return str(steam_id)
                            
                        # Alternative: look for steamid in different formats
                        steam_id = payload_data.get('steamid')
                        if steam_id and str(steam_id).isdigit() and len(str(steam_id)) == 17:
                            return str(steam_id)
                            
                    except Exception as e:
                        # Debug info
                        print(f"Debug - JWT decode error: {e}")
                        pass

        except Exception as e:
            print(f"Debug - JWT parsing error: {e}")
            pass

        return None

    def extract_steamid_from_token(self, token_string):
        """Extract Steam64 ID from various token formats"""
        try:
            # Try to extract from JWT format first
            steam_id = self.extract_steamid_from_jwt(token_string)
            if steam_id:
                return steam_id
                
            # Try to extract from regular cookie format
            if 'steamLoginSecure=' in token_string:
                # Extract everything after steamLoginSecure=
                match = re.search(r'steamLoginSecure=(.*)', token_string)
                if match:
                    secure_value = match.group(1)
                    # Try to get Steam ID from JWT inside the cookie
                    steam_id = self.extract_steamid_from_jwt(secure_value)
                    if steam_id:
                        return steam_id
            
            # If nothing works, try regex pattern matching for 17-digit numbers
            steam_id_match = re.search(r'(\d{17})', token_string)
            if steam_id_match:
                steam_id = steam_id_match.group(1)
                if len(steam_id) == 17:
                    return steam_id
                    
        except Exception as e:
            print(f"Debug - Token parsing error: {e}")
            pass

        return None

    def extract_steamid_from_cookies(self, cookies_dict):
        """Extract Steam64 ID from cookies"""
        steam_login_secure = cookies_dict.get('steamLoginSecure', '')

        if not steam_login_secure:
            # Try to find any cookie that looks like a Steam ID
            for key, value in cookies_dict.items():
                steam_id = self.extract_steamid_from_token(value)
                if steam_id:
                    return steam_id
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

    # ==================== ADD EXPIRATION EXTRACTION METHOD ====================
    def extract_expiration_from_cookies(self, cookies_dict):
        """Extract expiration timestamp from steamLoginSecure cookie (assuming JWT format)."""
        try:
            steam_login_secure = cookies_dict.get('steamLoginSecure', '')
            if not steam_login_secure:
                return None

            # JWTs are in the format header.payload.signature
            # The payload (middle part) contains the expiration information
            parts = steam_login_secure.split('.')
            if len(parts) >= 2:
                payload_b64 = parts[1]
                # Add padding if needed for base64 decoding
                payload_b64 += '=' * (4 - len(payload_b64) % 4)
                try:
                    payload_bytes = base64.urlsafe_b64decode(payload_b64)
                    payload_str = payload_bytes.decode('utf-8')
                    payload_data = json.loads(payload_str)

                    # Standard JWT expiration claim is 'exp'
                    exp_timestamp = payload_data.get('exp')
                    if isinstance(exp_timestamp, (int, float)) and exp_timestamp > 0:
                        return int(exp_timestamp) # Return as integer Unix timestamp
                except (base64.binascii.Error, json.JSONDecodeError, ValueError, TypeError):
                    # Decoding or parsing failed, might not be a standard JWT or malformed
                    pass
        except Exception as e:
            # General error during extraction
            print(f"  Warning: Could not extract expiration date from cookie: {e}")
            pass
        return None # Return None if not found or on error
    # =======================================================

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


# ==================== MODIFIED FUNCTION ====================
def generate_html_report(accounts, statistics, file_path):
    """Generate HTML report using the template module"""
    try:
        # Use the imported render_report function
        html_str = render_report(accounts, statistics, title="Steam Account Validation Report")

        # Write the generated HTML string to the output file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_str)

        print(f"HTML report saved to {file_path}")
    except Exception as e:
        print(f"Error generating HTML report: {e}")
# =======================================================


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
                # Try direct token parsing
                steam_id = session_manager.extract_steamid_from_token(token)
                if steam_id:
                    print(f"Steam ID (direct): {steam_id}")
                else:
                    print("No Steam ID found in token")

            # ==================== ADD EXPIRATION EXTRACTION ====================
            # Extract expiration date from the cookies
            token_expires_timestamp = session_manager.extract_expiration_from_cookies(cookies)
            # Format it for display, or indicate if not found
            if token_expires_timestamp:
                 # Use the existing format_timestamp helper
                token_expires_formatted = format_timestamp(token_expires_timestamp)
            else:
                token_expires_formatted = "Unknown/No Expire"
            print(f"Token Expires: {token_expires_formatted}")
            # =======================================================

            # Validate session (existing code continues...)
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

            # ==================== ADJUSTED DATA STRUCTURE ====================
            # Create account record matching the template's expected structure
            account = {
                "Account_Number": i,
                "Status": status, # Matches template key
                "SteamID": steam_id if steam_id else "Unknown", # Matches template key
                "Username": user_profile["username"], # Matches template key
                "Real_Name": user_profile["real_name"], # Matches template key
                "VAC_Banned": format_ban_status(ban_info["VACBanned"]), # Matches template key
                "Community_Banned": format_ban_status(ban_info["CommunityBanned"]), # Matches template key
                "Economy_Banned": ban_info["EconomyBan"], # Matches template key
                "VAC_Count": ban_info["NumberOfVACBans"], # Matches template key
                "Account_Created": format_timestamp(user_profile["time_created"]), # Matches template key
                "Last_Online": format_timestamp(user_profile["last_logoff"]), # Matches template key
                # ==================== ADD EXPIRES FIELD ====================
                "Expires": token_expires_formatted, # Add the formatted expiration date
                # =======================================================
                # Optional fields not used by template but kept for completeness
                "Profile_URL": user_profile["profile_url"],
                "Days_Since_Last_Ban": ban_info["DaysSinceLastBan"],
                "Game_Bans": ban_info["NumberOfGameBans"],
                "Persona_State": user_profile["persona_state"]
            }
            # =======================================================

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
            # ==================== ERROR DATA STRUCTURE ====================
            # Ensure error entries also match the template structure
            account = {
                "Account_Number": i,
                "Status": "Error", # Matches template key
                "SteamID": "Error", # Matches template key
                "Username": "Error", # Matches template key
                "Real_Name": "Error", # Matches template key
                "VAC_Banned": "Error", # Matches template key
                "Community_Banned": "Error", # Matches template key
                "Economy_Banned": "Error", # Matches template key
                "VAC_Count": 0, # Matches template key
                "Account_Created": "Error", # Matches template key
                "Last_Online": "Error", # Matches template key
                # ==================== ADD EXPIRES FIELD FOR ERROR ====================
                "Expires": "Error", # Add Expires field for consistency
                # =======================================================
                 # Optional fields not used by template but kept for completeness
                "Profile_URL": "",
                "Days_Since_Last_Ban": 0,
                "Game_Bans": 0,
                "Persona_State": 0
            }
            # =======================================================
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
    # ==================== CORRECTED CALCULATION ====================
    # Handle potential "Error" or other string values correctly
    vac_banned = sum(1 for a in accounts if str(a["VAC_Banned"]).strip().lower() == "yes")
    community_banned = sum(1 for a in accounts if str(a["Community_Banned"]).strip().lower() == "yes")
    economy_banned = sum(1 for a in accounts if str(a["Economy_Banned"]).strip().lower() not in ("none", "no_data", "error", "invalid_id", "no_steamid"))
    # =======================================================

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

    # ==================== CALL MODIFIED FUNCTION ====================
    # Generate HTML report using the template
    generate_html_report(accounts, statistics, OUTPUT_FILE)
    # =======================================================

    # Print completion message
    print("\nProcessing complete!")
    print(f"HTML report saved to: {OUTPUT_FILE}")
    print("Open the HTML file in any web browser for easy viewing")


if __name__ == "__main__":
    main()