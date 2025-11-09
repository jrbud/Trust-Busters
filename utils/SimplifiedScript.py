import re

import google.generativeai as genai
import csv
import os
from typing import Optional, Dict, List


class BrandAnalysis:
    def __init__(self, CompanyBrandFile: str, api_key: Optional[str] = None):

        # Load the brand-company mapping from CSV
        print(f"Loading brand data from {CompanyBrandFile}...")
        self.brand_to_company = {}  # {brand: company}
        self.company_to_brands = {}  # {company: [brands]}

        self._load_csv(CompanyBrandFile)

        print(f"Loaded {len(self.brand_to_company)} brands from {len(self.company_to_brands)} companies\n")

        # Set up Google AI for future query stuff
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv('GOOGLE_API_KEY')

        if not self.api_key:
            raise ValueError("API key required")

        genai.configure(api_key=self.api_key)
        self.model_name = self._find_best_model()
        print(f"Using AI model: {self.model_name}\n")
        self.model = genai.GenerativeModel(self.model_name)



    def _load_csv(self, csv_file: str):
        # Preps the csv data to be parsed and gets it into our dictionaries
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if 'Company' not in reader.fieldnames or 'Brand' not in reader.fieldnames:
                raise ValueError("CSV must have 'Company' and 'Brand' columns")

            for row in reader:
                company = row['Company'].strip()
                brand = row['Brand'].strip()

                # Clean data before adding !!
                if not company or not brand:
                    continue

                if brand == "NO_DATA":
                    continue

                # Store brand -> company mapping
                self.brand_to_company[re.sub(r'["\']', '', brand.lower())] = company

                # Store company -> brands mapping
                if company not in self.company_to_brands:
                    self.company_to_brands[re.sub(r'["\']', '', company)] = []
                if brand not in self.company_to_brands[re.sub(r'["\']', '', company)]:
                    self.company_to_brands[re.sub(r'["\']', '', company)].append(re.sub(r'["\']', '', brand.lower()))



    def _find_best_model(self) -> str:
        # Finds AI Model to use for query stuff
        # Try Gemini 2.0 Flash-Lite first (higher rate limits)
        preferred_models = ['gemini-2.0-flash-lite','models/gemini-2.0-flash-lite','gemini-1.5-flash','models/gemini-1.5-flash']

        try:
            available = [m.name for m in genai.list_models()
                         if 'generateContent' in m.supported_generation_methods]

            for preferred in preferred_models:
                for available_model in available:
                    if preferred in available_model.lower():
                        return available_model

            # Fallback to first available
            if available:
                return available[0]
        except:
            pass
        return 'models/gemini-2.0-flash-lite'



    def get_parent_company(self, brand_or_company: str) -> Optional[tuple]:
        # Gets parent company when given an input, used for lookups
        search_term = brand_or_company.lower()

        # Check if it's a brand
        if search_term in self.brand_to_company:
            return (self.brand_to_company[search_term], True)

        # Check if it's a company (exact match)
        for company in self.company_to_brands.keys():
            if company.lower() == search_term:
                return (company, False)

        # Try partial matching for brands
        brand_matches = [brand for brand in self.brand_to_company.keys()
                         if search_term in brand]
        if len(brand_matches) == 1:
            brand = list(self.brand_to_company.keys())[list(self.brand_to_company.keys()).index(brand_matches[0])]
            return (self.brand_to_company[brand_matches[0]], True)
        elif len(brand_matches) > 1:
            print(f"Multiple brand matches found for '{brand_or_company}':")
            for match in brand_matches:
                actual_brand = [b for b in self.brand_to_company.keys() if b == match][0]
                print(f"  - {actual_brand} → {self.brand_to_company[match]}")
            print("Please be more specific.\n")
            return None

        # Try partial matching for companies
        company_matches = [company for company in self.company_to_brands.keys()
                           if search_term in company.lower()]
        if len(company_matches) == 1:
            return (company_matches[0], False)
        elif len(company_matches) > 1:
            print(f"Multiple company matches found for '{brand_or_company}':")
            for match in company_matches:
                print(f"  - {match}")
            print("Please be more specific.\n")
            return None

        return None


    def get_graph_stats(self) -> str:
        # Function to display STATISTICS about the graph
        # For fun and for testing purposes


        result = "=== GRAPH STATISTICS ===\n"
        result += f"Total Companies: {len(self.company_to_brands.keys())}\n"
        result += f"Total Brands: {len(self.brand_to_company.keys())}\n"

        # Find company with most brands
        if self.company_to_brands.keys():
            max_brands = max(self.company_to_brands,key=lambda k: len(self.company_to_brands[k]))

            result += f"\nLargest Portfolio: {max_brands} "

        return result



    def analyze_company_donations(self, company_name: str) -> str:
        """
        Use AI to research and report on where a company donates money
        """
        prompt = f"""You are an ethical consumerism researcher. I need detailed, factual information about {company_name}'s donations and where their money goes.

Please provide:

1. **Political Donations & Lobbying**: What political causes, candidates, or lobbying efforts does {company_name} fund? Include specific amounts and years if available.

2. **Charitable Donations**: What charities, foundations, or causes does {company_name} support? Are these genuine charitable efforts or potentially problematic?

3. **Controversial Investments**: Does {company_name} invest in or support any controversial industries (fossil fuels, weapons, prison systems, etc.)?

4. **Labor & Ethics Issues**: Any known issues with labor practices, environmental damage, or ethical controversies where money is involved?

5. **Overall Ethical Assessment**: A brief summary of whether consumers should be aware of where their money goes when buying from {company_name}.

Please be factual, cite specific examples when possible, and present both positive and negative information. If certain information is not publicly available, please state that clearly."""

        try:
            print(f"🔍 Researching {company_name}'s financial activities...\n")
            response = self.model.generate_content(prompt, generation_config={'temperature': 0.3,  'max_output_tokens': 2048,})
            return response.text

        except Exception as e:
            return f"Error analyzing company: {e}"

    def analyze_brand(self, brand_or_company: str) -> str:
        # AI analysis script
        # Find the parent company
        result_tuple = self.get_parent_company(brand_or_company)

        if not result_tuple:
            return f"❌ Could not find '{brand_or_company}' in the database."

        company, is_brand = result_tuple

        # Get all brands owned by this company
        brand_labels = self.company_to_brands.get(company, [])

        # Build the report

        result = f"📦 You searched for: {brand_or_company}\n"

        if is_brand:
            result += f"🏷️  Type: Brand\n"
        else:
            result += f"🏷️  Type: Company\n"

        result += f"🏢 Parent Company: {company}\n"

        if brand_labels:
            result += f"🏪 Brands owned by {company} ({len(brand_labels)}): {', '.join(sorted(brand_labels))}\n"

        result += "\n" + "-" * 70 + "\n"
        result += "WHERE YOUR MONEY GOES:\n"
        result += "-" * 70 + "\n\n"

        # Get AI analysis
        analysis = self.analyze_company_donations(company)
        result += analysis

        result += "\n\n" + "=" * 70 + "\n"
        result += "💡 Remember: Every purchase is a vote for the kind of world you want to live in.\n"
        result += "=" * 70 + "\n"

        return result



    def quick_lookup(self, brand_or_company: str) -> str:
        # Normal lookup for normal searches !!
        # Takes a Brand or Company name and returns simple info
        result_tuple = self.get_parent_company(brand_or_company)

        if not result_tuple:
            return f"❌ Could not find '{brand_or_company}' in the database."

        company, is_brand = result_tuple

        # Get all brands owned by this company
        brand_labels = self.company_to_brands.get(company, [])

        # Build the report
        company, is_brand = result_tuple
        # Brand
        if is_brand:
            result = "Brand"
            result += "," + brand_or_company
            result += "," + company

            # Show sibling brands (other brands owned by same company)
            siblings = [b for b in brand_labels if b.lower() != brand_or_company.lower()]
            if siblings:
                for sibling in sorted(siblings):
                    result += "," + sibling
        # Company
        else:
            result = "Company"
            result += "," + brand_or_company
            brands = self.company_to_brands.get(company, [])
            for brand in sorted(brands):
                result += "," + brand

        return result



    def list_all_companies(self) -> str:
        """List all companies in the database"""
        companies = sorted(self.company_to_brands.keys())
        result = f"📊 Database contains {len(companies)} companies:\n\n"
        for company in companies:
            brand_count = len(self.company_to_brands[company])
            result += f"  • {company} ({brand_count} brands)\n"
        return result


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    API_KEY = "AIzaSyB8vI7n3836w4dWUvfxGviEokYhUe9ZV5E"  # Replace with your actual key
    CSV_FILE = "Test Files/webscrape.csv"  # Path to your CSV file



    try:
        analyzer = BrandAnalysis(CompanyBrandFile=CSV_FILE, api_key=API_KEY )

        print("\n\n")

        print("Example 2: Quick lookup")
        print("-" * 70)
        print(analyzer.quick_lookup("Pepsi"))

        print(analyzer.quick_lookup("PepsiCo"))

        print("\n\n")

        print(analyzer.get_graph_stats())

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set your Google AI API key")
        print("2. Provide the correct path to your CSV file")