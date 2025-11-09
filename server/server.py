from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from Utils.SimplifiedScript import BrandAnalysis

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/company', methods=['GET'])
def get_company_info():
    company = request.args.get('name')
    if not company:
        return jsonify({"error": "Missing company name"}), 400

    company_lower = company.lower()
    companyinfo = parse_lookup(company)
    data = next((v for k, v in companyinfo.items() if k.lower() == company_lower), None)

    if not data:
        return jsonify({"error": f"No data found for '{company}'"}), 404

    return jsonify(data)


def parse_lookup(company):
    analyzer = BrandAnalysis("csvfile", api_key=company)
    data = analyzer.quick_lookup(company)
    type = data.pop(0)
    name = data.pop(0)
    if type == "brand":
        parent = data.pop(0)
        return {"brand":name,"parent":parent,"sisters":data}
    return {"company": name, "children": data}
@app.route('/api/suggest', methods=['GET'])
def suggest_companies():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])

    matches = [name for name in sample_company if query in name.lower()]
    return jsonify(matches[:10])

if __name__ == '__main__':
    app.run(debug=True)