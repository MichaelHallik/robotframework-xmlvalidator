
"""
Module: fetch_pepy_downloads.py

This module fetches download statistics for a specific Python package
hosted on pepy.tech using the Pro API (which requires authentication),
and generates a badge (as an SVG file) representing the total number of downloads.

Features:
- Secure API access using a GitHub Actions secret.
- Aggregates download counts from the past year (including CI downloads).
- Outputs a static SVG badge suitable for embedding in README files.
"""

# Import the os module to access environment variables
import os

# Import the requests library to perform HTTP operations
import requests

# Define the base URL for the pepy.tech Pro API endpoint for project download stats
BASE_URL = "https://api.pepy.tech/service-api/v1/pro/projects/{package}/downloads"

# Construct the full URL for fetching download stats for the given package,
# including query parameters to include CI downloads and cover the last year
PEPY_API_URL = BASE_URL.format(package="robotframework-xmlvalidator") + "?includeCIDownloads=true&timeRange=ONE_YEAR"

# Define the name of the package to query on pepy.tech
PACKAGE_NAME = "robotframework-xmlvalidator"

# Fetch the API key from the environment variable; this must be configured in GitHub Secrets
API_KEY = os.getenv("PEPY_API_KEY")

# Define an SVG badge template with placeholders for the download count
SVG_BADGE_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="20">
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
"""

def fetch_download_count():
    """
    Fetch the total number of downloads for the specified package
    from the pepy.tech Pro API, aggregated over the past year
    and including CI downloads.

    Returns:
        str: A formatted string representing the total number of downloads
             (e.g., '12,345') for inclusion in an SVG badge.
    
    Raises:
        EnvironmentError: If the API key is not found in environment variables.
        Exception: If the API response status is 401, 403, or 404.
    """
    if not API_KEY:
        raise EnvironmentError("PEPY_API_KEY not set in environment variables.")

    headers = {
        "X-API-Key": API_KEY
    }

    url = PEPY_API_URL
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

    return f"{total:,}"  # e.g., '12,345'

def create_badge_svg(count, output_path="badge_pepy_downloads.svg"):
    """
    Generate an SVG badge using the total download count
    and save it to the specified output path.

    Args:
        count (str): The formatted string of total downloads.
        output_path (str): Path to the output SVG file (default: 'badge_pepy_downloads.svg').
    """
    svg_content = SVG_BADGE_TEMPLATE.format(count=count)
    with open(output_path, "w") as f:
        f.write(svg_content)
    print(f"Badge written to {output_path}")

if __name__ == "__main__":
    count = fetch_download_count()
    create_badge_svg(count)
