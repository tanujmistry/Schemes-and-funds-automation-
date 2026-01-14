import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
CSV_FILENAME = "Master_MedTech_Dashboard.csv"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'


def get_soup(url):
    """Helper to fetch page content safely."""
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=20, verify=False)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"❌ CONNECTION ERROR for {url}: {e}")
        return None


# --- SECTION 1: GOVERNMENT & MINISTRY ---

def scrape_birac():
    print("\n--- Scanning BIRAC (BIG, SBIRI, PACE) ---")
    url = "https://birac.nic.in/cfp.php"
    soup = get_soup(url)
    data = []
    if soup:
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    link_tag = cols[1].find('a')
                    if link_tag:
                        title = link_tag.text.strip()
                        href = link_tag['href']
                        if not href.startswith("http"): href = "https://birac.nic.in/" + href.lstrip('/')
                        data.append(
                            {"Organization": "BIRAC", "Category": "Government Grant", "Scheme": title, "Link": href})
    print(f"  ✅ BIRAC: Found {len(data)} calls.")
    return data


def scrape_icmr():
    print("\n--- Scanning ICMR (Clinical Trials) ---")
    url = "https://www.icmr.gov.in/call-for-proposals"
    soup = get_soup(url)
    data = []
    if soup:
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.text.strip()
            if any(k in text for k in ['Call', 'Proposal', 'Device', 'Diagnostic']) and len(text) > 10:
                href = link['href']
                if not href.startswith("http"): href = "https://www.icmr.gov.in/" + href.lstrip('/')
                data.append({"Organization": "ICMR", "Category": "Research Grant", "Scheme": text, "Link": href})
    print(f"  ✅ ICMR: Found {len(data)} calls.")
    return data


def scrape_pharma_dept():
    print("\n--- Scanning Dept of Pharmaceuticals (PLI/Parks) ---")
    url = "https://pharmaceuticals.gov.in/schemes"
    soup = get_soup(url)
    data = []
    if soup:
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.text.strip()
            if "Scheme" in text and ("Medical" in text or "PLI" in text):
                data.append(
                    {"Organization": "Dept of Pharma", "Category": "Subsidy/PLI", "Scheme": text, "Link": link['href']})
    print(f"  ✅ Dept of Pharma: Found {len(data)} schemes.")
    return data


# --- SECTION 2: INCUBATORS (IMPLEMENTING AGENCIES) ---
# NOTE: Incubators like C-CAMP often manage NIDHI-PRAYAS and TIDE 2.0 calls.

def scrape_ccamp():
    print("\n--- Scanning C-CAMP (Home of BIG & NIDHI) ---")
    url = "https://www.ccamp.res.in/"
    soup = get_soup(url)
    data = []
    if soup:
        # Check their news/scroll section or menu for active calls
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.text.strip()
            if any(k in text.upper() for k in ['BIG', 'CALL FOR', 'NIDHI', 'PRAYAS']):
                href = link['href']
                if not href.startswith("http"): href = "https://www.ccamp.res.in" + href
                data.append({"Organization": "C-CAMP", "Category": "Incubator Grant", "Scheme": text, "Link": href})
    print(f"  ✅ C-CAMP: Found {len(data)} updates.")
    return data


def scrape_venture_center():
    print("\n--- Scanning Venture Center (CSR & Seed Funds) ---")
    url = "https://www.venturecenter.co.in/funding"
    soup = get_soup(url)
    data = []
    if soup:
        links = soup.find_all('a', href=True)
        for link in links:
            text = link.text.strip()
            if any(k in text.lower() for k in ['apply', 'call', 'fund', 'seed']):
                href = link['href']
                if not href.startswith("http"): href = "https://www.venturecenter.co.in/" + href
                data.append(
                    {"Organization": "Venture Center", "Category": "Incubator/CSR", "Scheme": text, "Link": href})
    print(f"  ✅ Venture Center: Found {len(data)} opportunities.")
    return data


def scrape_social_alpha():
    print("\n--- Scanning Social Alpha (Impact/NGO) ---")
    url = "https://www.socialalpha.org/challenges/"
    soup = get_soup(url)
    data = []
    if soup:
        # Looking for challenge titles
        cards = soup.find_all(['h3', 'h4'])  # Headers often contain challenge names
        for card in cards:
            text = card.text.strip()
            if len(text) > 5:
                data.append(
                    {"Organization": "Social Alpha", "Category": "Impact Challenge", "Scheme": text, "Link": url})
    print(f"  ✅ Social Alpha: Found {len(data)} challenges.")
    return data


# --- SECTION 3: STATIC RESOURCES (TENDERS, CORPORATES, VCs) ---
# These sites are hard to scrape daily or don't change often.
# We add them permanently so the CSV is a complete reference.

def get_static_resources():
    return [
        # Government Tenders
        {"Organization": "GeM Portal", "Category": "Tenders", "Scheme": "Govt e-Marketplace (Search: Medical Devices)",
         "Link": "https://gem.gov.in/"},
        {"Organization": "CPPP Portal", "Category": "Tenders", "Scheme": "Central Procurement (Search: Hospital/Lab)",
         "Link": "https://eprocure.gov.in/cppp/"},

        # Ministry Schemes (Hard to scrape)
        {"Organization": "Startup India", "Category": "Seed Fund", "Scheme": "Startup India Seed Fund Scheme (SISFS)",
         "Link": "https://seedfund.startupindia.gov.in/"},
        {"Organization": "DST", "Category": "Grant", "Scheme": "NIDHI-PRAYAS (Apply via Incubators)",
         "Link": "https://nidhi-prayas.in/"},
        {"Organization": "MeitY", "Category": "Tech Grant", "Scheme": "TIDE 2.0 (Apply via C-CAMP/IITs)",
         "Link": "https://meitystartuphub.in/"},

        # Corporate Accelerators
        {"Organization": "Pfizer", "Category": "Corporate", "Scheme": "Pfizer INDovation",
         "Link": "https://www.socialalpha.org/pfizer-indovation/"},
        {"Organization": "Marico", "Category": "Corporate", "Scheme": "Marico Innovation Foundation (Scale-up)",
         "Link": "https://www.maricoinnovationfoundation.org/"},
        {"Organization": "GE Healthcare", "Category": "Corporate", "Scheme": "Edison Accelerator",
         "Link": "https://www.ge.com/in/edison-accelerator"},

        # VCs
        {"Organization": "HealthQuad", "Category": "VC", "Scheme": "Venture Capital Funding",
         "Link": "https://healthquadcapital.com/"},
        {"Organization": "W Health Ventures", "Category": "VC", "Scheme": "Venture Capital Funding",
         "Link": "https://whealthventures.com/"}
    ]


# --- MAIN CONTROLLER ---
def main():
    print("🚀 Starting Complete MedTech Ecosystem Scraper...")
    all_schemes = []

    # 1. Run Live Scrapers
    all_schemes.extend(scrape_birac())
    all_schemes.extend(scrape_icmr())
    all_schemes.extend(scrape_pharma_dept())
    all_schemes.extend(scrape_ccamp())
    all_schemes.extend(scrape_venture_center())
    all_schemes.extend(scrape_social_alpha())

    # 2. Add Static Resources (The "Directory")
    print("\n--- Adding Static Directories (Tenders, VCs, Corporates) ---")
    static_data = get_static_resources()
    all_schemes.extend(static_data)
    print(f"  ✅ Added {len(static_data)} permanent resources.")

    # 3. Save to CSV
    if all_schemes:
        df = pd.DataFrame(all_schemes)

        # Reorder columns for readability
        df = df[['Organization', 'Category', 'Scheme', 'Link']]

        # Remove duplicates (keeping the first occurrence)
        df.drop_duplicates(subset=['Link'], keep='first', inplace=True)

        try:
            df.to_csv(CSV_FILENAME, index=False)
            print(f"\n🎉 SUCCESS! Database updated with {len(df)} entries.")
            print(f"Saved to: {CSV_FILENAME}")
        except PermissionError:
            print(f"\n❌ ERROR: Please close '{CSV_FILENAME}' and try again.")
    else:
        print("\n⚠️ No data found.")


if __name__ == "__main__":
    main()
