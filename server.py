from flask import Flask, request
import networkx as nx
from pyvis.network import Network
import os

app = Flask(__name__)

# --- Sample dataset ---
COMPANIES = [
    {"brand": "Oreo", "company": "Mondelez", "industry": "Food"},
    {"brand": "Ritz", "company": "Mondelez", "industry": "Food"},
    {"brand": "Dove", "company": "Unilever", "industry": "Personal Care"},
    {"brand": "Axe", "company": "Unilever", "industry": "Personal Care"},
    {"brand": "Coca-Cola", "company": "Coca-Cola Co", "industry": "Beverage"},
    {"brand": "Sprite", "company": "Coca-Cola Co", "industry": "Beverage"},
    {"brand": "Pepsi", "company": "PepsiCo", "industry": "Beverage"},
    {"brand": "Doritos", "company": "PepsiCo", "industry": "Food"},
]

@app.route("/")
def index():
    query = request.args.get("query", "").lower()
    industry_filter = request.args.get("industry", "").lower()

    # Filter dataset
    results = [
        c for c in COMPANIES
        if (query in c["brand"].lower() or query in c["company"].lower())
        and (industry_filter in c["industry"].lower() if industry_filter else True)
    ]

    if not results:
        return f"<h2>No results found for '{query}' in '{industry_filter}'</h2>"

    # Build a graph
    G = nx.Graph()

    for item in results:
        brand = item["brand"]
        company = item["company"]
        industry = item["industry"]

        G.add_node(brand, title=f"Brand ({industry})", color="#90CAF9")
        G.add_node(company, title=f"Company ({industry})", color="#FFAB91")
        G.add_edge(brand, company, title="owned_by")

    # Create a PyVis network
    net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
    net.from_nx(G)
    net.show_buttons(filter_=['physics'])
    net.save_graph("templates/graph.html")

    return open("templates/graph.html", "r").read()

if __name__ == "__main__":
    print()
    os.makedirs("templates", exist_ok=True)
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True)
