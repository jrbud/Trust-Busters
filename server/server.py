from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample company data
sample_company = {
    "BrandX": {
        "company": "BrandX",
        "parent": "MegaCorp Inc.",
        "children": ["BrandX Kids", "BrandX Home", "BrandX Pro"],
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
    company = request.args.get('name')
    if not company:
        return jsonify({"error": "Missing company name"}), 400

    company_lower = company.lower()
    data = next((v for k, v in sample_company.items() if k.lower() == company_lower), None)

    if not data:
        return jsonify({"error": f"No data found for '{company}'"}), 404

    return jsonify(data)

@app.route('/api/suggest', methods=['GET'])
def suggest_companies():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])

    matches = [name for name in sample_company if query in name.lower()]
    return jsonify(matches[:10])

if __name__ == '__main__':
    app.run(debug=True)