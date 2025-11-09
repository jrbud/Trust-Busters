import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime
import time



def search_brand_list_page(company_name):
    search_api = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"List of {company_name} brands",
        "format": "json",
        "srlimit": 1
    }
    headers = {"User-Agent": "BrandScraper/3.1"}
    try:
        response = requests.get(search_api, params=params, headers=headers, timeout=10)
        data = response.json()
        if "query" in data and data["query"]["search"]:
            title = data["query"]["search"][0]["title"]
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            return title, url
    except:
        pass
    return None, None

''' IGNOTE THIS
def check_wikipedia_page_exists(page_title):
    """
    Check if a Wikipedia page actually exists (blue link).
    Returns True only if the page exists and is not a redirect to a non-existent page.
    """
    api_url = "https://en.wikipedia.org/w/api.php"

    import urllib.parse
    page_title = urllib.parse.unquote(page_title)
    params = {
        "action": "query",
        "titles": page_title,
        "format": "json",
        "redirects": 1
    }
    headers = {"User-Agent": "BrandScraper/3.1"}
    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=5)
        data = response.json()

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if page_id == "-1":
                return False  # Page doesn't exist (red link)
            if "missing" in page_data:
                return False  # Page is missing
            return True  # Page exists (blue link)

    except Exception as e:
        print(f"          API check failed for {page_title}, assuming valid")
        return True

    return False

'''

def is_brand_section(header_text):
    header_lower = header_text.lower()
    exclude_keywords = [
        'partnership', 'joint venture', 'licensing', 'distribution',
        'franchise', 'collaboration', 'alliance', 'agreement',
        'see also', 'reference', 'external link', 'note', 'citation'
    ]
    if any(keyword in header_lower for keyword in exclude_keywords):
        return False
    return True


def is_generic_description(text):
    #Trash generics
    generic_terms = [
        'ice cream', 'frozen dessert', 'tea', 'instant coffee', 'oolong tea',
        'green tea', 'black tea', 'bottled water', 'mineral water', 'spring water',
        'laundry detergent', 'sweet soy sauce', 'soy sauce', 'stain remover',
        'bathroom tissue', 'moist towelette', 'personal care',
        'soft drink', 'soft drinks', 'energy drink', 'sports drink',
        'fruit juice', 'orange juice', 'juice', 'water',
        'cola', 'soda', 'beverage', 'drink', 'food',
        'soap', 'shampoo', 'conditioner', 'deodorant', 'toothpaste',
        'detergent', 'cleanser', 'lotion', 'cream',
        'snack', 'cereal', 'candy', 'chocolate',
        'julmust', 'peace tea'
    ]
    generic_phrases = ['available in', 'sold in', 'marketed as', 'type of', 'brand of']
    if text in generic_terms or any(phrase in text for phrase in generic_phrases):
        return True
    return False

def extract_brands(url):
    headers = {"User-Agent": "BrandScraper/3.1"}
    brands = {}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print("Failed to fetch page: {e}")
        return set()
    content = soup.find("div", {"id": "mw-content-text"})
    if not content:
        return set()
    in_brand_section = False
    potential_brands = []  # Collect all potential brands first
    for element in content.find_all(["h2", "h3", "h4", "h5", "h6", "li"]):
        if element.name in ["h2", "h3", "h4", "h5", "h6"]:
            header_text = element.get_text(strip=True)
            if is_brand_section(header_text):
                in_brand_section = True
                print(" Found section: {header_text}")
            else:
                in_brand_section = False
            continue
        if element.name == "li" and in_brand_section:
            if element.find_parent(["nav", "footer"]) or element.find_parent("div", {"class": ["navbox", "reflist"]}):
                continue
            text = element.get_text(strip=True)
            text_lower = text.lower()
            if any(word in text_lower for word in ["divested", "sold to", "discontinued"]):
                continue
            brand_name = None
            wiki_link = None
            all_links = element.find_all("a", href=lambda h: h and h.startswith("/wiki/") and ":" not in h)
            for link in all_links:
                if "new" in link.get("class", []):
                    continue
                link_text = link.get_text(strip=True)
                if not is_generic_description(link_text.lower()):
                    href = link.get("href", "")
                    wiki_title = href.replace("/wiki/", "")
                    brand_name = link_text
                    wiki_link = wiki_title
                    break

            #check for linked page
            if not brand_name:
                bold = element.find(["b", "strong"])
                if bold:
                    bold_link = bold.find("a", href=lambda h: h and h.startswith("/wiki/") and ":" not in h)
                    if bold_link and "new" not in bold_link.get("class", []):
                        brand_name = bold.get_text(strip=True)
                        href = bold_link.get("href", "")
                        wiki_link = href.replace("/wiki/", "")

            # Storing and strip split
            if brand_name and wiki_link:
                brand_name = brand_name.split('[')[0].split('(')[0].strip()
                brand_name = brand_name.strip(" ,.–—")
                if not is_generic_description(brand_name.lower()) and 1 < len(brand_name) < 60:
                    potential_brands.append((brand_name, wiki_link))

    # extract BOLD links
    for table in content.find_all("table", {"class": "wikitable"}):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue

            # first cell
            first_cell = cells[0]
            link = first_cell.find("a", href=lambda h: h and h.startswith("/wiki/") and ":" not in h)

            if link and "new" not in link.get("class", []):
                text = link.get_text(strip=True)
                if text and not is_generic_description(text.lower()):
                    brand_name = text.split('[')[0].split('(')[0].strip()
                    brand_name = brand_name.strip(" ,.–—")
                    if 1 < len(brand_name) < 60:
                        href = link.get("href", "")
                        wiki_link = href.replace("/wiki/", "")
                        potential_brands.append((brand_name, wiki_link))

    # WikipediaAPI
    print(f"      → Validating {len(potential_brands)} potential brands...")

    if not potential_brands:
        return set()

    #remove duplicates
    seen = set()
    unique_brands = []
    for brand_name, wiki_link in potential_brands:
        if wiki_link not in seen:
            seen.add(wiki_link)
            unique_brands.append((brand_name, wiki_link))


    validated_brands = set()
    batch_size = 50

    for i in range(0, len(unique_brands), batch_size):
        batch = unique_brands[i:i + batch_size]

        # Titles
        titles = [wiki_link for _, wiki_link in batch]
        titles_str = "|".join(titles)

        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "titles": titles_str,
            "format": "json",
            "redirects": 1
        }
        headers = {"User-Agent": "BrandScraper/3.1"}

        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            data = response.json()

            pages = data.get("query", {}).get("pages", {})

            # What pages exist
            existing_titles = set()
            for page_id, page_data in pages.items():
                if page_id != "-1" and "missing" not in page_data:
                    # Get the actual title (handles redirects)
                    title = page_data.get("title", "")
                    existing_titles.add(title.replace(" ", "_"))

            # Match brands to exisiting pages
            for brand_name, wiki_link in batch:
                import urllib.parse
                decoded_link = urllib.parse.unquote(wiki_link)

                # CHECK SAGAIN
                if (wiki_link in existing_titles or
                        decoded_link in existing_titles or
                        wiki_link.replace("_", " ") in [t.replace("_", " ") for t in existing_titles]):
                    validated_brands.add(brand_name)
                else:
                    print("BAD NEWS: Skipped no page: {brand_name}")

        except Exception as e:
            print("Batch validation failed, accepting all in batch: {e}")
            # Give up if batch fails
            for brand_name, _ in batch:
                validated_brands.add(brand_name)

        # delays
        if i + batch_size < len(unique_brands):
            time.sleep(0.3)

    return validated_brands



def scrape_companies_to_csv(company_list, output_filename=None):
    #Scraping brands for list of companies
    #needs to be valid wikipage
    # returns csv file path

    if output_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") # I HAVE NO IDEA WHAT THIS DOES
        output_filename = f"brands_{timestamp}.csv"

    print("Company Brand Scraper - Blue Links Only")
    print("=" * 50)
    print("Processing {len(company_list)} companies...")
    print("Output file: {output_filename}")
    print("=" * 50)

    # stats
    stats = {
        'total': len(company_list),
        'found': 0,
        'no_page': 0,
        'no_brands': 0,
        'total_brands': 0
    }

    # writing csv
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['CompanyName', 'BrandName'])  # Header

        #process each company
        for i, company in enumerate(company_list, 1):
            print(f"\n[{i}/{len(company_list)}] Processing: {company}")
            print("-" * 50)

            # search for the company
            title, url = search_brand_list_page(company)

            if not url:
                print(" No 'List of brands' page found")
                writer.writerow([company, "NO_DATA"])
                stats['no_page'] += 1
                continue

            print(f"   ✓ Found: {title}")

            #extract brands
            brands = extract_brands(url)

            if brands:
                print("Validated {len(brands)} brands with Wikipedia pages")
                stats['found'] += 1
                stats['total_brands'] += len(brands)
                # new row
                for brand in sorted(brands):
                    writer.writerow([company, brand])
            else:
                print("NO DATA ERROR !!!!!!!!!!!")
                writer.writerow([company, "NO_DATA"])
                stats['no_brands'] += 1

    print("\n" + "=" * 50)
    print("SUCCESS!!!!!!! {output_filename}")
    print("=" * 50)
    print("\n stats:")
    print("   Total: {stats['total']}")
    print("   NO BRANDS MANUAL CHECK: {stats['no_brands']}")
    print("=" * 50)

    return output_filename

# main
if __name__ == "__main__":
    print("Company Brand Scraper - Blue Links Only Version")
    print("=" * 50)

    #list of top 100 companies according to
    companies = [
        "Nestlé", "LVMH", "PepsiCo", "Procter & Gamble", "JBS S.A.",
        "Unilever", "Anheuser-Busch InBev", "Tyson Foods", "Nike",
        "Coca-Cola Company", "L'Oréal", "Heineken", "Imperial Tobacco",
        "Haier", "Mondelez International", "Philip Morris International",
        "British American Tobacco", "3M", "Danone", "Kraft Heinz",
        "WH Group", "Altria Group", "Associated British Foods",
        "Henkel", "Grupo Bimbo", "Kering", "Richemont", "Diageo",
        "Kimberly-Clark", "General Mills", "Japan Tobacco",
        "Colgate-Palmolive", "Whirlpool", "Asahi Group Holdings",
        "Reckitt Benckiser", "Yili Group", "Kellogg", "Estée Lauder",
        "Stanley Black & Decker", "BSH Hausgeräte", "Johnson & Johnson",
        "Fonterra", "Uni-President Enterprises", "Arla Foods",
        "Kirin Holdings", "Hermès", "Keurig Dr Pepper",
        "Royal FrieslandCampina", "Essity", "Halon",
        "China Mengniu Dairy", "Saputo", "Pernod Ricard",
        "Electrolux", "Hormel Foods", "Nintendo",
        "Molson Coors Brewing", "VF Corporation", "Hershey",
        "BRF", "Carlsberg", "Kao Corporation",
        "First Pacific", "Beiersdorf", "Danish Crown",
        "Constellation Brands", "Campbell Soup", "PVH",
        "Groupe SEB", "Swatch Group", "NH Foods",
        "J.M. Smucker", "Thai Beverage", "ITC Limited",
        "Abbott Laboratories", "Newell Brands", "Skechers",
        "Makro", "Arçelik", "Savencia", "Electronic Arts",
        "Clorox", "Post Holdings", "Shiseido",
        "Bandai Namco", "San Miguel Corporation", "Bayer",
        "Unicharm", "McCormick & Company", "Tapestry",
        "Ralph Lauren", "Levi Strauss", "Under Armour",
        "Church & Dwight", "Hanesbrands", "Coty", "Mattel",
        "Adidas", "Puma", "Revlon"
    ]


    print("Press Enter to start scraping...")
    input()

    output_file = scrape_companies_to_csv(companies)
    print(" FINISHED !")