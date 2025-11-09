import csv
from datetime import datetime


def clean_brand_name(brand):
    # remove white space and quotations
    brand = brand.replace('"', '').replace("'", '').strip()

    # enociding issues
    encoding_fixes = {
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã§': 'ç',
        'Ã¢': 'â',
        'Ã´': 'ô',
        'Ã¯': 'ï',
        'Ã«': 'ë',
        'Ã ': 'à',
        'Ãª': 'ê',
        'Ã¼': 'ü',
        'Ã¶': 'ö',
        'Ã±': 'ñ',
        'Ã³': 'ó',
        'Ã¡': 'á',
        'Ã­': 'í',
        'Ãº': 'ú',
        'Å': 'Š',
        'Ä': 'Č',
        'â€"': '–',
        'â€™': "'",
    }

    for bad, good in encoding_fixes.items():
        brand = brand.replace(bad, good)

    # Capitalize first letter but watchign out for McDonald and shitl ike this
    words = brand.split()
    cleaned_words = []
    for word in words:
        if word.islower():
            cleaned_words.append(word.capitalize())
        else:
            cleaned_words.append(word)

    return ' '.join(cleaned_words)


def clean_company_name(company):
    # Fix encoding issues
    encoding_fixes = {
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã§': 'ç',
        'Ã¢': 'â',
        'Ã´': 'ô',
        'Ã¯': 'ï',
        'Ã«': 'ë',
        'Ã ': 'à',
        'Ãª': 'ê',
        'Ã¼': 'ü',
        'Ã¶': 'ö',
        'Ã±': 'ñ',
        'Ã³': 'ó',
        'Ã¡': 'á',
        'Ã­': 'í',
        'Ãº': 'ú',
        'Å': 'Š',
        'Ä': 'Č',
    }

    for bad, good in encoding_fixes.items():
        company = company.replace(bad, good)

    return company.strip()


def clean_csv(input_file, output_file=None):
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"cleaned_{timestamp}.csv"
    print("-" * 50)
    print("Input file: {input_file}")
    print("Output file: {output_file}")
    print("-" * 50)

    unique_entries = set()
    rows_to_write = []

    # Read input file
    print("\n📖 Reading input file...")
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)  # Skip header

        for row in reader:
            if len(row) < 2:
                continue

            company = clean_company_name(row[0])
            brand = clean_brand_name(row[1])

            # Skip NO_DATA entries
            if brand.upper() == 'NO_DATA':
                continue


            unique_key = (company.lower(), brand.lower())

            if unique_key not in unique_entries:
                unique_entries.add(unique_key)
                rows_to_write.append([company, brand])

    rows_to_write.sort(key=lambda x: (x[0], x[1]))


    # Write cleaned file
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['CompanyName', 'BrandName'])  # Write header
        writer.writerows(rows_to_write)


    return output_file


if __name__ == "__main__":
    # Replace with your input filename
    input_filename = "Old Scraped Files/brands_20251108_173221.csv"

    print("-" * 50)

    print("CSV CLEANER: Enter")
    input()

    output = clean_csv(input_filename)
    print("DONE.")