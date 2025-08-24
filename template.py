from datetime import datetime
from html import escape

def _status_class(status: str) -> str:
    status = (status or "").lower()
    if status == "valid":
        return "status-valid"
    if status == "invalid":
        return "status-invalid"
    return "status-error"

def _ban_class(value: str, kind: str) -> str:
    if kind in ("vac", "community"):
        return "ban-yes" if (value or "").strip().lower() == "yes" else "ban-no"
    if kind == "economy":
        v = (value or "").strip().lower()
        return "ban-yes" if v not in ("none", "no_data", "error") else "ban-no"
    return ""

def render_report(accounts, stats, *, title: str = "Steam Account Validation Report", generated_at: datetime | None = None) -> str:
    generated_at = generated_at or datetime.now()

    def esc(x):
        return escape(str(x if x is not None else ""))

    total = int(stats.get("total", len(accounts)))
    valid = int(stats.get("valid", 0))
    invalid = int(stats.get("invalid", 0))
    vac_banned = int(stats.get("vac_banned", 0))
    community_banned = int(stats.get("community_banned", 0))
    economy_banned = int(stats.get("economy_banned", 0))

    rows_html = []
    for a in accounts:
        # Check if Profile_URL exists and create appropriate HTML
        profile_url = a.get('Profile_URL', '')
        if profile_url:
            profile_link = f'<a href="{profile_url}" target="_blank" style="color: #03a9f4; text-decoration: underline;">View</a>'
        else:
            profile_link = "N/A"
            
        rows_html.append(
            f"""
            <tr>
                <td class="account-number">{esc(a.get('Account_Number', ''))}</td>
                <td class="{_status_class(a.get('Status', ''))}">{esc(a.get('Status', ''))}</td>
                <td>{esc(a.get('SteamID', ''))}</td>
                <td>{esc(a.get('Username', ''))}</td>
                <td>{esc(a.get('Real_Name', ''))}</td>
                <td class="{_ban_class(a.get('VAC_Banned', 'No'), 'vac')}">{esc(a.get('VAC_Banned', 'No'))}</td>
                <td class="{_ban_class(a.get('Community_Banned', 'No'), 'community')}">{esc(a.get('Community_Banned', 'No'))}</td>
                <td class="{_ban_class(a.get('Economy_Banned', 'none'), 'economy')}">{esc(a.get('Economy_Banned', 'none'))}</td>
                <td>{esc(a.get('VAC_Count', 0))}</td>
                <td>{esc(a.get('Account_Created', 'Never'))}</td>
                <td>{esc(a.get('Last_Online', 'Never'))}</td>
                <td>{esc(a.get('Expires', 'Unknown'))}</td>
                <td>{profile_link}</td>
            </tr>
            """
        )
    rows = "\n".join(rows_html)

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{esc(title)}</title>
    <style>
        body {{
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #121212;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: #1e1e1e;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 25px rgba(0,0,0,0.5);
        }}
        h1 {{
            color: #00bcd4;
            text-align: center;
            border-bottom: 2px solid #00bcd4;
            padding-bottom: 10px;
        }}
        .summary {{
            background: linear-gradient(135deg, #1f2937, #111827);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #00bcd4;
            text-align: center;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
        }}
        .summary-item {{
            background-color: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .summary-item:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        }}
        .summary-value {{
            font-size: 26px;
            font-weight: bold;
            color: #00e676;
        }}
        .summary-label {{
            font-size: 14px;
            color: #aaa;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            overflow: hidden;
            border-radius: 10px;
        }}
        th, td {{
            padding: 12px 14px;
            text-align: left;
        }}
        th {{
            background-color: #00bcd4;
            color: #fff;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #2a2a2a;
        }}
        tr:nth-child(odd) {{
            background-color: #242424;
        }}
        tr:hover {{
            background-color: #333333;
        }}
        .status-valid {{ color: #00e676; font-weight: bold; }}
        .status-invalid {{ color: #ff5252; font-weight: bold; }}
        .status-error {{ color: #ffc107; font-weight: bold; }}
        .ban-yes {{ color: #ff5252; font-weight: bold; }}
        .ban-no {{ color: #00e676; }}
        .account-number {{ font-weight: bold; color: #03a9f4; }}
        .header-section p {{ color: #bbb; margin: 5px 0; text-align:center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-section">
            <h1>{esc(title)}</h1>
            <p>Generated on: {esc(generated_at.strftime('%Y-%m-%d %H:%M:%S'))}</p>
            <p>Report contains information about Steam accounts and their ban status</p>
        </div>

        <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="summary-grid">
                <div class="summary-item"><div class="summary-value">{total}</div><div class="summary-label">Total Accounts</div></div>
                <div class="summary-item"><div class="summary-value">{valid}</div><div class="summary-label">Valid Accounts</div></div>
                <div class="summary-item"><div class="summary-value">{invalid}</div><div class="summary-label">Invalid Accounts</div></div>
                <div class="summary-item"><div class="summary-value">{vac_banned}</div><div class="summary-label">VAC Banned</div></div>
                <div class="summary-item"><div class="summary-value">{community_banned}</div><div class="summary-label">Community Banned</div></div>
                <div class="summary-item"><div class="summary-value">{economy_banned}</div><div class="summary-label">Economy Banned</div></div>
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
                    <th>Expires</th>
                    <th>Profile</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return html