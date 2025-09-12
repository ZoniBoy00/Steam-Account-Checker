#!/usr/bin/env python3
"""
Enhanced Steam Account Checker with JWT Token Validation
Validates Steam session tokens, checks account status, and generates detailed reports.
"""

import requests
import json
import time
import re
import urllib.parse
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Import the render_report function from the template module
from template import render_report

# ==================== CONFIGURATION ====================
STEAM_API_KEY = "YOUR_STEAM_WEB_API_KEY"  # Replace with your actual Steam Web API key
INPUT_FILE = "tokens.json"            # File containing Steam session cookies in JSON format
OUTPUT_FILE = "steam_account_report.html"
DELAY_BETWEEN_REQUESTS = 2            # Seconds between requests (reduced for efficiency)
REQUEST_TIMEOUT = 10                  # Request timeout in seconds
MAX_RETRIES = 3                       # Maximum retry attempts for failed requests
# =======================================================

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('steam_checker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
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
    """Handles Steam API interactions and session management with optimized performance"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=requests.adapters.Retry(
                total=MAX_RETRIES,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def parse_token_format(self, token_string: str) -> Dict[str, Any]:
        """Parse token in username----JWT format or regular cookie format"""
        token_info = {
            'username': None,
            'jwt_token': None,
            'cookies': {},
            'raw_token': token_string
        }
        
        try:
            # Handle username----JWT format
            if '----' in token_string:
                parts = token_string.split('----', 1)
                if len(parts) == 2:
                    token_info['username'] = parts[0].strip()
                    token_info['jwt_token'] = parts[1].strip()
                    token_info['cookies']['steamLoginSecure'] = token_info['jwt_token']
                    return token_info
            
            # Handle steamLoginSecure= format
            if 'steamLoginSecure=' in token_string:
                match = re.search(r'steamLoginSecure=([^;]+)', token_string)
                if match:
                    jwt_value = match.group(1).strip()
                    token_info['jwt_token'] = jwt_value
                    token_info['cookies']['steamLoginSecure'] = jwt_value
                    
                    username = self._extract_username_from_jwt(jwt_value)
                    if username:
                        token_info['username'] = username
                    
                    return token_info
            
            # Handle direct JWT token
            if token_string.count('.') == 2:  # JWT format
                token_info['jwt_token'] = token_string.strip()
                token_info['cookies']['steamLoginSecure'] = token_string.strip()
                
                username = self._extract_username_from_jwt(token_string)
                if username:
                    token_info['username'] = username
                
                return token_info
            
            # Fallback: parse as cookie string
            token_info['cookies'] = self._parse_cookies_from_line(token_string)
            
        except Exception as e:
            logger.error(f"Error parsing token format: {e}")
        
        return token_info

    def _extract_username_from_jwt(self, jwt_token: str) -> Optional[str]:
        """Extract username/persona name from JWT payload"""
        try:
            parts = jwt_token.split('.')
            if len(parts) >= 2:
                payload_part = parts[1]
                payload_part += '=' * (4 - len(payload_part) % 4)
                
                payload_bytes = base64.urlsafe_b64decode(payload_part)
                payload_str = payload_bytes.decode('utf-8')
                payload_data = json.loads(payload_str)
                
                # Look for username-like fields
                for field in ['username', 'name', 'persona', 'personaname']:
                    if field in payload_data:
                        return payload_data[field]
                        
        except Exception:
            pass
        return None

    def validate_jwt_token(self, jwt_token: str) -> Dict[str, Any]:
        """Validate JWT token and extract information with enhanced error handling"""
        validation_result = {
            'is_valid': False,
            'is_expired': False,
            'steam_id': None,
            'username': None,
            'expires_at': None,
            'issued_at': None,
            'error': None,
            'payload': None
        }
        
        try:
            parts = jwt_token.split('.')
            if len(parts) != 3:
                validation_result['error'] = "Invalid JWT format"
                return validation_result
            
            # Decode payload
            payload_part = parts[1]
            payload_part += '=' * (4 - len(payload_part) % 4)
            
            payload_bytes = base64.urlsafe_b64decode(payload_part)
            payload_str = payload_bytes.decode('utf-8')
            payload_data = json.loads(payload_str)
            
            validation_result['payload'] = payload_data
            
            # Extract Steam ID
            steam_id = payload_data.get('sub')
            if steam_id and str(steam_id).isdigit() and len(str(steam_id)) == 17:
                validation_result['steam_id'] = str(steam_id)
            
            # Extract expiration
            exp_timestamp = payload_data.get('exp')
            if exp_timestamp:
                validation_result['expires_at'] = exp_timestamp
                current_time = int(time.time())
                validation_result['is_expired'] = current_time > exp_timestamp
            
            # Extract issued at
            iat_timestamp = payload_data.get('iat')
            if iat_timestamp:
                validation_result['issued_at'] = iat_timestamp
            
            # Check if token is structurally valid and not expired
            validation_result['is_valid'] = (
                validation_result['steam_id'] is not None and 
                not validation_result['is_expired']
            )
            
            if validation_result['is_expired']:
                validation_result['error'] = "Token has expired"
            elif not validation_result['steam_id']:
                validation_result['error'] = "No valid Steam ID found in token"
            
        except Exception as e:
            validation_result['error'] = f"JWT parsing error: {str(e)}"
        
        return validation_result

    def _parse_cookies_from_line(self, cookie_line: str) -> Dict[str, str]:
        """Parse cookie line into dictionary"""
        cookies = {}
        if not cookie_line:
            return cookies

        parts = cookie_line.strip().split(';')
        for part in parts:
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                cookies[key.strip()] = value.strip()
        return cookies

    def _extract_steamid_from_jwt(self, jwt_string: str) -> Optional[str]:
        """Extract Steam64 ID from JWT token with improved error handling"""
        try:
            if '%' in jwt_string:
                jwt_string = urllib.parse.unquote(jwt_string)

            if '||' in jwt_string:
                parts = jwt_string.split('||')
                if len(parts) >= 2:
                    steam_id = parts[0]
                    if steam_id.isdigit() and len(steam_id) == 17:
                        return steam_id

            if '.' in jwt_string:
                parts = jwt_string.split('.')
                if len(parts) >= 2:
                    payload_part = parts[1]
                    payload_part += '=' * (4 - len(payload_part) % 4)
                    
                    try:
                        payload_bytes = base64.urlsafe_b64decode(payload_part)
                        payload_str = payload_bytes.decode('utf-8')
                        payload_data = json.loads(payload_str)
                        
                        steam_id = payload_data.get('sub') or payload_data.get('steamid')
                        if steam_id and str(steam_id).isdigit() and len(str(steam_id)) == 17:
                            return str(steam_id)
                            
                    except Exception as e:
                        logger.debug(f"JWT decode error: {e}")

        except Exception as e:
            logger.debug(f"JWT parsing error: {e}")

        return None

    def extract_steamid_from_token(self, token_string: str) -> Optional[str]:
        """Extract Steam64 ID from various token formats"""
        try:
            steam_id = self._extract_steamid_from_jwt(token_string)
            if steam_id:
                return steam_id
                
            if 'steamLoginSecure=' in token_string:
                match = re.search(r'steamLoginSecure=(.*)', token_string)
                if match:
                    secure_value = match.group(1)
                    steam_id = self._extract_steamid_from_jwt(secure_value)
                    if steam_id:
                        return steam_id
            
            steam_id_match = re.search(r'(\d{17})', token_string)
            if steam_id_match:
                steam_id = steam_id_match.group(1)
                if len(steam_id) == 17:
                    return steam_id
                    
        except Exception as e:
            logger.debug(f"Token parsing error: {e}")

        return None

    def extract_steamid_from_cookies(self, cookies_dict: Dict[str, str]) -> Optional[str]:
        """Extract Steam64 ID from cookies"""
        steam_login_secure = cookies_dict.get('steamLoginSecure', '')

        if not steam_login_secure:
            for key, value in cookies_dict.items():
                steam_id = self.extract_steamid_from_token(value)
                if steam_id:
                    return steam_id
            return None

        steam_id = self._extract_steamid_from_jwt(steam_login_secure)

        if not steam_id:
            try:
                decoded_value = urllib.parse.unquote(steam_login_secure)
                steam_id_match = re.search(r'(\d{17})', decoded_value)
                if steam_id_match:
                    steam_id = steam_id_match.group(1)
            except:
                pass

        if steam_id and steam_id.isdigit() and len(steam_id) == 17:
            return steam_id
        else:
            return None

    def extract_expiration_from_cookies(self, cookies_dict: Dict[str, str]) -> Optional[int]:
        """Extract expiration timestamp from steamLoginSecure cookie"""
        try:
            steam_login_secure = cookies_dict.get('steamLoginSecure', '')
            if not steam_login_secure:
                return None

            parts = steam_login_secure.split('.')
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += '=' * (4 - len(payload_b64) % 4)
                try:
                    payload_bytes = base64.urlsafe_b64decode(payload_b64)
                    payload_str = payload_bytes.decode('utf-8')
                    payload_data = json.loads(payload_str)

                    exp_timestamp = payload_data.get('exp')
                    if isinstance(exp_timestamp, (int, float)) and exp_timestamp > 0:
                        return int(exp_timestamp)
                except (base64.binascii.Error, json.JSONDecodeError, ValueError, TypeError):
                    pass
        except Exception as e:
            logger.warning(f"Could not extract expiration date from cookie: {e}")
        return None

    def validate_session_with_cookies(self, cookies_dict: Dict[str, str]) -> Dict[str, Any]:
        """Validate session by making a request to Steam with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                self.session.cookies.clear()

                for key, value in cookies_dict.items():
                    self.session.cookies.set(key, value)

                test_url = "https://store.steampowered.com/account/"
                response = self.session.get(test_url, timeout=REQUEST_TIMEOUT)

                is_logged_in = any(keyword in response.text.lower() for keyword in 
                                 ['logout', 'account settings', 'welcome', 'profile', 'dashboard'])

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
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    return {
                        "is_valid": False,
                        "status_code": 0,
                        "response_length": 0,
                        "error": str(e)
                    }
                time.sleep(1)  # Wait before retry

    def get_user_profile(self, steam_id: str) -> Dict[str, Any]:
        """Get user profile information using Steam Web API with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
                params = {
                    "key": STEAM_API_KEY,
                    "steamids": steam_id
                }

                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()

                data = response.json()

                if ("response" in data and "players" in data["response"] and 
                    len(data["response"]["players"]) > 0):
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

            except Exception as e:
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    logger.error(f"Failed to get user profile for {steam_id}: {e}")
                    break
                time.sleep(1)  # Wait before retry

        return {
            "username": "Unknown",
            "real_name": "Not specified",
            "avatar": "",
            "profile_url": "",
            "time_created": 0,
            "last_logoff": 0,
            "persona_state": 0
        }

    def check_bans_for_steamid(self, steam_id: str) -> Dict[str, Any]:
        """Check bans for a given Steam64 ID using Steam Web API with retry logic"""
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

        for attempt in range(MAX_RETRIES):
            try:
                url = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
                params = {
                    "key": STEAM_API_KEY,
                    "steamids": steam_id
                }

                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
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

            except Exception as e:
                if attempt == MAX_RETRIES - 1:  # Last attempt
                    logger.error(f"Failed to check bans for {steam_id}: {e}")
                    break
                time.sleep(1)  # Wait before retry

        return {
            "VACBanned": False,
            "CommunityBanned": False,
            "EconomyBan": "error",
            "NumberOfVACBans": 0,
            "DaysSinceLastBan": 0,
            "NumberOfGameBans": 0,
            "SteamID": ""
        }


def read_tokens_from_json(file_path: str) -> List[str]:
    """Read tokens from JSON file with improved error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tokens = []
        if isinstance(data, list):
            tokens = [token.strip() for token in data if token.strip()]
        elif isinstance(data, dict):
            if 'tokens' in data:
                tokens = [token.strip() for token in data['tokens'] if token.strip()]
            else:
                for key, value in data.items():
                    if isinstance(value, list):
                        tokens.extend([item.strip() for item in value if item.strip()])
                        break
                if not tokens and 'token' in data:
                    tokens = [data['token'].strip()] if data['token'].strip() else []
        else:
            tokens = [data.strip()] if data.strip() else []

        logger.info(f"Found {len(tokens)} tokens in JSON file")
        return tokens
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        return []


def format_timestamp(timestamp: int) -> str:
    """Convert Unix timestamp to readable date"""
    if timestamp and timestamp > 0:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    return "Never"


def format_ban_status(banned: bool) -> str:
    """Format ban status for display"""
    return "Yes" if banned else "No"


def generate_html_report(accounts: List[Dict], statistics: Dict, file_path: str) -> None:
    """Generate HTML report using the template module"""
    try:
        html_str = render_report(accounts, statistics, title="Steam Account Validation Report")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_str)

        logger.info(f"HTML report saved to {file_path}")
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")


def process_accounts(tokens: List[str]) -> List[Dict]:
    """Process all Steam accounts and return account data with progress tracking"""
    session_manager = SteamSessionManager()
    accounts = []
    total_tokens = len(tokens)

    for i, token in enumerate(tokens, 1):
        logger.info(f"Processing Account #{i} of {total_tokens}")
        print(f"\nProcessing Account #{i} of {total_tokens}")
        print("-" * 40)
        print(f"Raw Token: {token[:80]}{'...' if len(token) > 80 else ''}")

        try:
            token_info = session_manager.parse_token_format(token)
            
            if token_info['username']:
                print(f"Username from token: {token_info['username']}")
            
            jwt_validation = None
            if token_info['jwt_token']:
                jwt_validation = session_manager.validate_jwt_token(token_info['jwt_token'])
                print(f"JWT Valid: {jwt_validation['is_valid']}")
                print(f"JWT Expired: {jwt_validation['is_expired']}")
                if jwt_validation['error']:
                    print(f"JWT Error: {jwt_validation['error']}")

            cookies = token_info['cookies'] if token_info['cookies'] else session_manager._parse_cookies_from_line(token)

            # Extract Steam64 ID
            steam_id = None
            if jwt_validation and jwt_validation['steam_id']:
                steam_id = jwt_validation['steam_id']
                print(f"Steam ID (from JWT): {steam_id}")
            else:
                steam_id = session_manager.extract_steamid_from_cookies(cookies)
                if steam_id:
                    print(f"Steam ID (from cookies): {steam_id}")
                else:
                    steam_id = session_manager.extract_steamid_from_token(token)
                    if steam_id:
                        print(f"Steam ID (direct): {steam_id}")
                    else:
                        print("No Steam ID found in token")

            # Extract expiration date
            token_expires_timestamp = None
            if jwt_validation and jwt_validation['expires_at']:
                token_expires_timestamp = jwt_validation['expires_at']
            else:
                token_expires_timestamp = session_manager.extract_expiration_from_cookies(cookies)
            
            token_expires_formatted = format_timestamp(token_expires_timestamp) if token_expires_timestamp else "Unknown/No Expire"
            print(f"Token Expires: {token_expires_formatted}")

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
                
                if token_info['username'] and user_profile['username'] in ['Unknown', 'Error']:
                    user_profile['username'] = token_info['username']
            else:
                print("Skipping ban and profile checks due to missing Steam ID")

            # Determine status
            status = "Valid"
            if jwt_validation:
                if jwt_validation['is_expired']:
                    status = "Expired"
                elif not jwt_validation['is_valid']:
                    status = "Invalid JWT"
                elif not session_result["is_valid"]:
                    status = "Session Invalid"
            elif not session_result["is_valid"]:
                status = "Invalid"

            # Create account record
            account = {
                "Account_Number": i,
                "Status": status,
                "SteamID": steam_id if steam_id else "Unknown",
                "Username": user_profile["username"],
                "Real_Name": user_profile["real_name"],
                "VAC_Banned": format_ban_status(ban_info["VACBanned"]),
                "Community_Banned": format_ban_status(ban_info["CommunityBanned"]),
                "Economy_Banned": ban_info["EconomyBan"],
                "VAC_Count": ban_info["NumberOfVACBans"],
                "Account_Created": format_timestamp(user_profile["time_created"]),
                "Last_Online": format_timestamp(user_profile["last_logoff"]),
                "Expires": token_expires_formatted,
                "JWT_Valid": "Yes" if jwt_validation and jwt_validation['is_valid'] else "No" if jwt_validation else "N/A",
                "JWT_Expired": "Yes" if jwt_validation and jwt_validation['is_expired'] else "No" if jwt_validation else "N/A",
                "Profile_URL": user_profile["profile_url"],
                "Days_Since_Last_Ban": ban_info["DaysSinceLastBan"],
                "Game_Bans": ban_info["NumberOfGameBans"],
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
            logger.error(f"Error processing token #{i}: {e}")
            account = {
                "Account_Number": i,
                "Status": "Error",
                "SteamID": "Error",
                "Username": "Error",
                "Real_Name": "Error",
                "VAC_Banned": "Error",
                "Community_Banned": "Error",
                "Economy_Banned": "Error",
                "VAC_Count": 0,
                "Account_Created": "Error",
                "Last_Online": "Error",
                "Expires": "Error",
                "JWT_Valid": "Error",
                "JWT_Expired": "Error",
                "Profile_URL": "",
                "Days_Since_Last_Ban": 0,
                "Game_Bans": 0,
                "Persona_State": 0
            }
            accounts.append(account)

        # Add delay to avoid rate limiting
        if i < len(tokens):
            print(f"Waiting {DELAY_BETWEEN_REQUESTS} seconds before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    return accounts


def calculate_statistics(accounts: List[Dict]) -> Dict[str, int]:
    """Calculate summary statistics with improved accuracy"""
    total_accounts = len(accounts)
    valid_accounts = sum(1 for a in accounts if a["Status"] == "Valid")
    invalid_accounts = sum(1 for a in accounts if a["Status"] in ["Invalid", "Session Invalid"])
    expired_accounts = sum(1 for a in accounts if a["Status"] == "Expired")
    jwt_valid_accounts = sum(1 for a in accounts if str(a["JWT_Valid"]).strip().lower() == "yes")
    
    vac_banned = sum(1 for a in accounts if str(a["VAC_Banned"]).strip().lower() == "yes")
    community_banned = sum(1 for a in accounts if str(a["Community_Banned"]).strip().lower() == "yes")
    economy_banned = sum(1 for a in accounts if str(a["Economy_Banned"]).strip().lower() not in 
                        ("none", "no_data", "error", "invalid_id", "no_steamid"))

    return {
        "total": total_accounts,
        "valid": valid_accounts,
        "invalid": invalid_accounts,
        "expired": expired_accounts,
        "jwt_valid": jwt_valid_accounts,
        "vac_banned": vac_banned,
        "community_banned": community_banned,
        "economy_banned": economy_banned
    }


def display_summary(statistics: Dict[str, int]) -> None:
    """Display summary statistics"""
    print("\n" + "=" * 60)
    print("FINAL RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Accounts Checked: {statistics['total']}")
    print(f"Valid Accounts: {statistics['valid']}")
    print(f"Invalid Accounts: {statistics['invalid']}")
    print(f"Expired Accounts: {statistics['expired']}")
    print(f"JWT Valid Accounts: {statistics['jwt_valid']}")
    print(f"VAC Banned Accounts: {statistics['vac_banned']}")
    print(f"Community Banned Accounts: {statistics['community_banned']}")
    print(f"Economy Banned Accounts: {statistics['economy_banned']}")
    print("=" * 60)


def validate_config() -> bool:
    """Validate configuration before running"""
    if STEAM_API_KEY == "YOUR_STEAM_API_KEY":
        logger.error("Please set your Steam API key in the STEAM_API_KEY variable")
        return False
    
    if not INPUT_FILE:
        logger.error("Input file not specified")
        return False
    
    return True


def main():
    """Main execution function with improved error handling"""
    print("=" * 60)
    print("STEAM ACCOUNT VALIDATOR & BAN CHECKER")
    print("=" * 60)
    
    # Validate configuration
    if not validate_config():
        return
    
    print(f"Using Steam API Key: {STEAM_API_KEY[:10]}... (hidden for security)")
    print(f"Input File: {INPUT_FILE}")
    print(f"Output File: {OUTPUT_FILE}")
    print("=" * 60)

    # Read tokens
    tokens = read_tokens_from_json(INPUT_FILE)

    if not tokens:
        logger.error("No tokens found in tokens.json")
        return

    logger.info(f"Processing {len(tokens)} Steam accounts...")

    # Process accounts
    accounts = process_accounts(tokens)

    # Calculate statistics
    statistics = calculate_statistics(accounts)

    # Display summary
    display_summary(statistics)

    # Generate HTML report
    generate_html_report(accounts, statistics, OUTPUT_FILE)

    # Print completion message
    print("\nProcessing complete!")
    print(f"HTML report saved to: {OUTPUT_FILE}")
    print("Open the HTML file in any web browser for easy viewing")
    logger.info("Steam account checking completed successfully")


if __name__ == "__main__":
    main()
