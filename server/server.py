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

# Route to serve the frontend
@app.route('/')
def home():
    return render_template('index.html')

# API endpoint to get company info
@app.route('/api/company', methods=['GET'])
def get_company_info():
    company = request.args.get('name')
    if not company:
        return jsonify({"error": "Missing company name"}), 400

    data = sample_company.get(company)
    if not data:
        return jsonify({"error": f"No data found for '{company}'"}), 404

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)