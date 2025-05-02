import os
import requests

PEPY_API_URL = "https://api.pepy.tech/service-api/v1/pro/projects/{package}/downloads"
PACKAGE_NAME = "robotframework-xmlvalidator"
API_KEY = os.getenv("PEPY_API_KEY")

SVG_BADGE_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="20">
  <linearGradient id="a" x2="0" y2="100%%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="200" height="20" fill="#555"/>
  <rect rx="3" x="70" width="130" height="20" fill="#4c1"/>
  <path fill="#4c1" d="M70 0h4v20h-4z"/>
  <rect rx="3" width="200" height="20" fill="url(#a)"/>
  <g fill="#fff" text-anchor="middle"
     font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="35" y="15" fill="#010101" fill-opacity=".3">downloads</text>
    <text x="35" y="14">downloads</text>
    <text x="135" y="15" fill="#010101" fill-opacity=".3">{count}</text>
    <text x="135" y="14">{count}</text>
  </g>
</svg>
'''

def fetch_download_count():
    if not API_KEY:
        raise EnvironmentError("PEPY_API_KEY not set in environment variables.")

    headers = {
        "X-API-Key": API_KEY
    }

    url = PEPY_API_URL.format(package=PACKAGE_NAME)
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        raise Exception(f"Package '{PACKAGE_NAME}' not found on pepy.tech Pro API.")
    elif response.status_code == 403:
        raise Exception("Access denied: Are you sure your account has Pro access?")
    elif response.status_code == 401:
        raise Exception("Unauthorized: Check that your API key is valid.")
    response.raise_for_status()

    data = response.json()
    total = 0
    for day, versions in data.get("downloads", {}).items():
        total += sum(versions.values())

    return f"{total:,}"  # e.g., 12,345

def create_badge_svg(count, output_path="badge_pepy_downloads.svg"):
    svg_content = SVG_BADGE_TEMPLATE.format(count=count)
    with open(output_path, "w") as f:
        f.write(svg_content)
    print(f"Badge written to {output_path}")

if __name__ == "__main__":
    count = fetch_download_count()
    create_badge_svg(count)
