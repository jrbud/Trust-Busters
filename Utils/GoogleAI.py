import google.generativeai as genai
import os
from typing import Optional, List, Dict

import google.generativeai as genai
import networkx as nx
import os
from typing import Optional, Dict

class EthicalBrandAnalyzer:
    def __init__(self, graph_file: str, api_key: Optional[str] = None):

        # Load the brand graph
        print("Loading brand graph...")
        self.graph = nx.read_gexf(graph_file)
        print(f"Loaded {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges\n")

        # Set up Google AI
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

    def _find_best_model(self) -> str:
        """Find the best available model"""
        try:
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    return model.name
        except:
            pass
        return 'models/gemini-1.5-flash'

    def find_node_by_label(self, name: str) -> Optional[tuple]:
        """Find a node by its label"""
        name_lower = name.lower()
        matches = []

        for node, attrs in self.graph.nodes(data=True):
            label = attrs.get('label', '')
            if name_lower in label.lower():
                matches.append((node, label, attrs.get('type')))

        return matches

    def get_parent_company(self, brand_or_company: str) -> Optional[str]:
        """
        Get the parent company for a brand or company name
        Returns the company name (or itself if already a company)
        """
        matches = self.find_node_by_label(brand_or_company)

        if not matches:
            return None

        if len(matches) > 1:
            print(f"Multiple matches found for '{brand_or_company}':")
            for _, label, node_type in matches:
                print(f"  - {label} ({node_type})")
            print("Please be more specific.\n")
            return None

        node_id, label, node_type = matches[0]

        # If it's already a company, return it
        if node_type == 'Company':
            return label

        # If it's a brand, find parent
        parent_ids = list(self.graph.predecessors(node_id))
        if parent_ids:
            parent_label = self.graph.nodes[parent_ids[0]].get('label')
            return parent_label

        return None

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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,  # Lower temperature for more factual responses
                    'max_output_tokens': 2048,
                }
            )
            return response.text

        except Exception as e:
            return f"Error analyzing company: {e}"

    def analyze_brand(self, brand_or_company: str) -> str:
        """
        Main function: Analyze a brand or company's ethical profile
        """
        # Find the parent company
        company = self.get_parent_company(brand_or_company)

        if not company:
            return f"❌ Could not find '{brand_or_company}' in the database."

        # Get all brands owned by this company
        matches = self.find_node_by_label(company)
        if matches:
            company_node_id = matches[0][0]
            owned_brands = list(self.graph.successors(company_node_id))
            brand_labels = [self.graph.nodes[bid].get('label') for bid in owned_brands]
        else:
            brand_labels = []

        # Build the report
        result = "=" * 70 + "\n"
        result += f"💰 ETHICAL MONEY TRAIL REPORT\n"
        result += "=" * 70 + "\n\n"

        result += f"📦 You searched for: {brand_or_company}\n"
        result += f"🏢 Parent Company: {company}\n"

        if brand_labels:
            result += f"🏪 Brands owned by {company}: {', '.join(sorted(brand_labels))}\n"

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
        """
        Quick lookup to see what company owns a brand
        """
        company = self.get_parent_company(brand_or_company)

        if not company:
            return f"❌ Could not find '{brand_or_company}' in the database."

        return f"🏢 {brand_or_company} → {company}"


# Example usage
if __name__ == "__main__":
    # Initialize the analyzer
    API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual key
    GRAPH_FILE = "Graphs/testGraph.gexf"  # Path to your graph file

    try:
        analyzer = EthicalBrandAnalyzer(
            graph_file=GRAPH_FILE,
            api_key=API_KEY
        )

        print("=" * 70)
        print("🌍 ETHICAL CONSUMERISM ANALYZER")
        print("=" * 70)
        print("Discover where your money really goes when you buy from brands.\n")

        # Example analysis
        print("Example 1: Analyzing Doritos (a brand)")
        print("-" * 70)
        report = analyzer.analyze_brand("Doritos")
        print(report)

        print("\n\n")

        print("Example 2: Quick lookup")
        print("-" * 70)
        print(analyzer.quick_lookup("Pepsi"))

        print("\n\n")

        # Interactive mode
        print("=" * 70)
        print("INTERACTIVE MODE")
        print("=" * 70)
        print("Commands:")
        print("  - Enter any brand or company name for full ethical analysis")
        print("  - Type 'quick [brand]' for quick parent company lookup")
        print("  - Type 'quit' to exit\n")

        while True:
            user_input = input("🔍 Search: ").strip()

            if user_input.lower() == 'quit':
                print("\nThank you for being a conscious consumer! 🌱")
                break

            if user_input.lower().startswith('quick '):
                brand = user_input[6:].strip()
                print(analyzer.quick_lookup(brand))
            elif user_input:
                print("\n")
                print(analyzer.analyze_brand(user_input))

            print("\n")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure to:")
        print("1. Set your Google AI API key")
        print("2. Provide the correct path to your GEXF graph file")