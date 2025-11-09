import csv
import re
from collections import defaultdict

with open("Old Scraped Files/company_brands (1).csv", 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    all_company_names = [row['CompanyName'].strip() for row in rows]
    all_brand_names = [row['BrandName'].strip() for row in rows]

with open("Old Scraped Files/brand_products2.csv", 'r', encoding='utf-8') as fp:
    reader = csv.DictReader(fp)
    product_names = {row['ProductName'].strip() for row in reader if row['ProductName'].strip()}

filtered_companies = []
filtered_brands = []
for company, brand in zip(all_company_names, all_brand_names):
    if brand not in product_names:
        filtered_companies.append(company)
        filtered_brands.append(brand)

with open("Old Scraped Files/company_brands_scrubbed2.csv", 'w', newline='', encoding='utf-8') as fp:
    fieldnames = ['CompanyName', 'BrandName']
    writer = csv.DictWriter(fp, fieldnames=fieldnames)
    writer.writeheader()
    for i in range(len(filtered_brands)):
        writer.writerow({
            'CompanyName': filtered_companies[i],
            'BrandName': filtered_brands[i]
        })

