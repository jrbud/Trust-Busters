import csv
import re
import os
from typing import Optional
import google.generativeai as genai
from PIL import Image


class BrandAnalysis:
    def __init__(self, companyBrandFile: str, brandProductFile: Optional[str]=None, APIKEY: Optional[str] = None):
        # Load the mappings from CSV
        self.brand2Company = {}
        self.company2brands = {}
        self.brand2Products = {}

        self.loadCSV(companyBrandFile)

        if brandProductFile:
            print(f"Loading product data from {brandProductFile}...")
            self.loadProductsCSV(brandProductFile)

        # Set up Google AI for future query stuff
        if APIKEY is not None:
            self.APIKEY = APIKEY
        else:
            self.APIKEY = os.getenv('GOOGLE_API_KEY')

        if not self.APIKEY:
            raise ValueError("API key required")

        genai.configure(api_key=self.APIKEY)
        self.model_name = self.chooseModel()
        self.model = genai.GenerativeModel(self.model_name)
        self.vision_model = self.model


    def loadCSV(self, filename: str):
        # Preps the csv data to be parsed and gets it into our dictionaries
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if 'Company' not in reader.fieldnames or 'Brand' not in reader.fieldnames:
                raise ValueError("CSV columns must be named 'Company' and 'Brand'")

            for row in reader:
                company = row['Company'].strip()
                brand = row['Brand'].strip()

                # Clean data before adding !!
                if not company or not brand or brand == "NO_DATA":
                    continue

                # Add mappings to Dicts !!
                # B2C and C2B
                self.brand2Company[re.sub(r'["\']', '', brand.lower())] = company

                if company not in self.company2brands:
                    self.company2brands[re.sub(r'["\']', '', company)] = []
                if brand not in self.company2brands[re.sub(r'["\']', '', company)]:
                    self.company2brands[re.sub(r'["\']', '', company)].append(re.sub(r'["\']', '', brand))

    def loadProductsCSV(self, filename: str):
        """Load brand-product relationships from CSV"""
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            if 'Brand' not in reader.fieldnames or 'Product' not in reader.fieldnames:
                raise ValueError("Products CSV must have 'Brand' and 'Product' columns")

            for row in reader:
                brand = row['Brand'].strip()
                product = row['Product'].strip()

                if not brand or not product:
                    continue

                # Add mappings to Dicts !!
                # B2P
                if brand not in self.brand2Products:
                    self.brand2Products[brand] = []
                if product not in self.brand2Products[brand]:
                    self.brand2Products[brand].append(product)

    def getParentCompany(self, brandOrCompany: str) -> Optional[tuple]:
        # Gets parent company when given an input, used for lookups
        # Returns parent company (input = branch), nothing (input = company), or a list of possible partial matches (input != match)
        searchTerm = brandOrCompany.lower()

        # Check if it's a brand
        if searchTerm in self.brand2Company:
            return (self.brand2Company[searchTerm], True, brandOrCompany)

        for brand, products in self.brand2Products.items():
            if any(searchTerm in product.lower() for product in products):
                matchingProducts = [p for p in products if searchTerm in p.lower()]
                if len(matchingProducts) == 1:

                    # Found a unique product, return its brand's company
                    company = self.brand2Company.get(brand.lower())
                    if company:
                        return (company, True, brand)
                elif len(matchingProducts) > 1:
                    print(f"Multiple products found matching '{brandOrCompany}':")
                    for prod in matchingProducts:
                        print(f"  - {prod} (Brand: {brand})")
                    print("Please be more specific.\n")
                    return None

        # Check if it's a company
        for company in self.company2brands.keys():
            if company.lower() == searchTerm:
                return (company, False, company)

        # Partial match to get other possible options, useful for autofill/suggesstions
        brandMatches = [brand for brand in self.brand2Company.keys() if searchTerm in brand]
        if len(brandMatches) == 1:
            brand = list(self.brand2Company.keys())[list(self.brand2Company.keys()).index(brandMatches[0])]
            return (self.brand2Company[brandMatches[0]], True)

        elif len(brandMatches) > 1:
            print(f"Multiple brand matches found for '{brandOrCompany}':")
            for match in brandMatches:
                actual_brand = [b for b in self.brand2Company.keys() if b == match][0]
                print(f"  - {actual_brand} → {self.brand2Company[match]}")
            print("Please be more specific.\n")
            return None

        company_matches = [company for company in self.company2brands.keys()if searchTerm in company.lower()]
        if len(company_matches) == 1:
            return (company_matches[0], False)

        elif len(company_matches) > 1:
            print(f"Multiple company matches found for '{brandOrCompany}':")
            for match in company_matches:
                print(f"  - {match}")
            print("Please be more specific.\n")
            return None

        return None


    def quickLookup(self, brandOrCompany: str) -> str:
        # Normal lookup for normal searches !!
        # Returns type,name,parent(input = brand), sibling/children
        resultTup = self.getParentCompany(brandOrCompany)

        if not resultTup:
            return f"Could not find '{brandOrCompany}' in the database."

        company, isBrand, matchedName = resultTup

        # Get all brands owned by this company
        brandLabels = self.company2brands.get(company, [])


        # Brand
        if isBrand:
            result = "Brand"
            result += "," + brandOrCompany
            result += "," + company

            # Return sibling brands
            siblings = [b for b in brandLabels if b.lower() != brandOrCompany.lower()]
            if siblings:
                for sibling in sorted(siblings):
                    result += "," + sibling
        # Company
        else:
            result = "Company"
            result += "," + brandOrCompany
            brands = self.company2brands.get(company, [])
            for brand in sorted(brands):
                result += "," + brand

        return result

#                          Testing Functions !!                          #
# -----------------------------------------------------------------------#

    def getStatistics(self) -> str:
        # Function to display STATISTICS about the graph
        # For fun and for testing purposes
        result = "=== GRAPH STATISTICS ===\n"
        result += f"Total Companies: {len(self.company2brands.keys())}\n"
        result += f"Total Brands: {len(self.brand2Company.keys())}\n"

        # Find company with most brands
        if self.company2brands.keys():
            biggestCompany = max(self.company2brands,key=lambda k: len(self.company2brands[k]))

            result += f"\nLargest Portfolio: {biggestCompany}"
        return result


    def listAllCompanies(self) -> str:
        # Just lists all the companies in the database
        # May get too long when data gets heavier but helpful for checking that formatting is correct
        companies = sorted(self.company2brands.keys())
        result = f"📊 Our database contains {len(companies)} companies:\n\n"
        for company in companies:
            brandCount = len(self.company2brands[company])
            result += f"  • {company} ({brandCount} brands)\n"
        return result
# -----------------------------------------------------------------------#



#                              AI Stuff !!                          #
#-----------------------------------------------------------------------#

    def chooseModel(self) -> str:
        # Finds good AI Model to use for query stuff
        # Want Gemini 2.0 Flash-Lite the most (higher rate limits)
        preferredModels = ['gemini-2.0-flash-lite','models/gemini-2.0-flash-lite','gemini-1.5-flash','models/gemini-1.5-flash']

        try:
            # Find all available models from API Key and return most preferred option
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

            for preferred in preferredModels:
                for availableModel in available:
                    if preferred in availableModel.lower():
                        return availableModel

            # If nothing preferred works just use the first option :/
            if available:
                return available[0]
        except:
            pass
        return 'models/gemini-2.0-flash-lite'


    def brandFromImage(self, image_path: str) -> Optional[str]:
        # Takes in an image and uses AI to identify the Brand !!! (SO COOL)
            try:
                # Load the image
                img = Image.open(image_path)

                # Get all brands to make AI's life(???) easier
                allBrands = list(self.brand2Company.keys())
                allCompanies = list(self.company2brands.keys())

                # AI prompt to get desired output, want it to return just the brand name and nothing else
                prompt = f"""Look at this product image and identify the brand name. 
                Known brands in our database: {', '.join(allBrands[:50])}... Known companies: {', '.join(allCompanies)}

                Please respond with ONLY the brand name or company name that appears on this product.
                If you see multiple brands, list the main/primary brand first.
                Just give me the brand name, nothing else."""

                response = self.vision_model.generate_content([prompt, img])
                identifiedBrand = response.text.strip()

                return identifiedBrand

            except FileNotFoundError:
                print(f"Error: Image file '{image_path}' not found")
                return None
            except Exception as e:
                print(f"Error identifying brand from image: {e}")
                return None

    def analyzeCompanyDonations(self, company_name: str) -> str:
       # Takes in a Company and tells user about the ethics of it
        prompt = f"""You are an ethical consumerism researcher. I need detailed, factual information about {company_name}'s donations and where their money goes.
        Please provide:
        1. Political Donations & Lobbying: What political causes, candidates, or lobbying efforts does {company_name} fund? Include specific amounts and years if available.
        2. Charitable Donations: What charities, foundations, or causes does {company_name} support? Are these genuine charitable efforts or potentially problematic?
        3. Controversial Investments: Does {company_name} invest in or support any controversial industries (fossil fuels, weapons, prison systems, etc.)?
        4. Labor & Ethics Issues: Any known issues with labor practices, environmental damage, or ethical controversies where money is involved?    
        5. Overall Ethical Assessment: A brief summary of whether consumers should be aware of where their money goes when buying from {company_name}.

        Please be factual, cite specific examples when possible, and present both positive and negative information. If certain information is not publicly available, please state that clearly."""

        try:
            response = self.model.generate_content(prompt,generation_config={'temperature': 0.3,  'max_output_tokens': 2048,})
            return response.text

        except Exception as e:
            return f"Error analyzing company: {e}"

#-----------------------------------------------------------------------#


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    API_KEY = "AIzaSyB8vI7n3836w4dWUvfxGviEokYhUe9ZV5E"
    CSVFILE = "../webscraping/company_brands_scrubbed2.csv"
    ProductCSVFILE = "../webscraping/brand_products2.csv"


    try:
        analyzer = BrandAnalysis(companyBrandFile=CSVFILE,brandProductFile=ProductCSVFILE, APIKEY=API_KEY )

        print("\n\n")

        print("Quick lookup")
        print("-" * 70)
        print(analyzer.quickLookup("Pepsi"))

        print("Quick lookup")
        print("-" * 70)
        print(analyzer.quickLookup("Diet Coke"))

        print("\n\n")

        print(analyzer.getStatistics())




    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set your Google AI API key")
        print("2. Provide the correct path to your CSV file")