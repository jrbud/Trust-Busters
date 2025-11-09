from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from Utils.SimplifiedScript import BrandAnalysis

analyzer = BrandAnalysis("webscraping/company_brands_scrubbed2.csv", "webscraping/brand_products2.csv",
                         APIKEY="AIzaSyB8vI7n3836w4dWUvfxGviEokYhUe9ZV5E")

app = Flask(__name__)
CORS(app)

# Sample company data
sample_company = {
    "BrandX": {
        "company": "BrandX",
        "parent": "MegaCorp Inc.",
        "children":["BrandX Kids", "BrandX Home", "BrandX Pro"],
        "sisters": ["BrandY", "BrandZ", "BrandW"]
    },
    "BrandY": {
        "company": "BrandY",
        "parent": "MegaCorp Inc.",
        "children": [],
        "sisters": ["BrandX", "BrandZ", "BrandW"]
    },
    "BrandZ": {
        "company": "BrandZ",
        "parent": "MegaCorp Inc.",
        "children": [],
        "sisters": ["BrandX", "BrandY", "BrandW"]
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/company', methods=['GET'])
def get_company_info():
    company = request.args.get('name').lower()
    print("GETTING COMPANY ",company)
    if not company:
        return jsonify({"error": "Missing company name"}), 400
    # data = next((v for k, v in sample_company.items() if k.lower() == company), None)
    # print(data)
    # print(sample_company["BrandX"])
    data = parse_lookup(company)
    print(data)
    if not data:
        return jsonify({"error": f"No data found for '{company}'"}), 404

    return jsonify(data)

@app.route('/ai-check',methods=['GET'])
def ai_check():
    company = request.args.get('name').lower()
    analyzer = BrandAnalysis("webscraping/company_brands_scrubbed2.csv","webscraping/brand_products2.csv", APIKEY="AIzaSyB8vI7n3836w4dWUvfxGviEokYhUe9ZV5E")
    return analyzer.analyzeCompanyDonations(company)

def parse_lookup(company):
    print("PARSING COMPANY")
    analyzer = BrandAnalysis("webscraping/company_brands_scrubbed2.csv","webscraping/brand_products2.csv", APIKEY="AIzaSyB8vI7n3836w4dWUvfxGviEokYhUe9ZV5E")
    if not analyzer:
        print("analyzer found nothing")
        return
    data = analyzer.quickLookup(company).split(",")
    company = parent =  ""
    children = sisters = []
    out = {"type":data.pop(0).lower(),"company": company, "parent": parent, "children": children, "sisters": sisters, "len":0}
    out["company"] = data.pop(0)
    print(out["type"])
    print("HIIII")
    print(out)

    if out["type"] == "brand":
        print("brand")

        parent = data.pop(0)
        out["parent"] = parent
        out["sisters"] = data
        out["len"] = len(data)
        print(out)
        return out
    elif out["type"] == "company":

        out["children"] = data
        out["len"] = len(data)
        print("company")
        print(out)
        return out

@app.route('/api/suggest', methods=['GET'])
def suggest_companies():
    query = request.args.get('q', '').lower()

    if not query:
        return jsonify([])

    suggestions = analyzer.partialMatch(query)
    matches = [name for name in suggestions if name.lower().startswith(query)]
    return jsonify(matches[:10])

if __name__ == '__main__':
    app.run(debug=True)