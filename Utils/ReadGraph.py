import networkx as nx
from typing import List, Dict, Optional



class BrandGraph:

    def __init__(this, FileName: Optional[str] = None):
        # takes an input of a GEXF FileName and converts it to DirectedGraph "this"
        if FileName:
            # Load existing graph from file
            this.graph = nx.read_gexf(FileName)
        else:
            # Create a new directed graph (company -> brand)
            this.graph = nx.DiGraph()


    def get_node_type(self, name: str) -> Optional[str]:
        """Get the type of a node (company or brand)"""
        # Search by label, not by node ID
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get('label', '').lower() == name.lower():
                return attrs.get('type')
        return None


    def find_node_id_by_label(self, name: str) -> Optional[str]:
        """Find the node ID by searching for the label"""
        name_lower = name.lower()
        for node, attrs in self.graph.nodes(data=True):
            label = attrs.get('label', '')
            if name_lower in label.lower():
                return node
        return None

    def query(self, name: str) -> str:
        # Function to QUERY the graph based on the name of a brand or company
        name_lower = name.lower()

        # Find all matches by label
        matches = []
        for node, attrs in self.graph.nodes(data=True):
            label = attrs.get('label', '')
            if name_lower in label.lower():
                matches.append((node, label, attrs.get('type')))

        if not matches:
            return f"'{name}' is not yet in our database :("

        # If multiple matches, show them all
        if len(matches) > 1:
            result = f"Found {len(matches)} matches:\n"
            for node_id, label, node_type in matches:
                result += f"\n{label} ({node_type})"
            return result

        # If one match...
        node_id, label, node_type = matches[0]
        result = f"Name: {label}\nType: {node_type.capitalize()}\n"

        # If input is a Company
        if node_type == 'Company':
            # Get all brands owned by this company (successors)
            owned_brand_ids = list(self.graph.successors(node_id))
            if owned_brand_ids:
                result += f"\nOwned Brands ({len(owned_brand_ids)}):\n"
                brand_labels = [self.graph.nodes[bid].get('label') for bid in owned_brand_ids]
                for brand_label in sorted(brand_labels):
                    result += f"  - {brand_label}\n"
            else:
                result += "\nNo brands registered for this company.\n"

        # If input is a Brand
        else:
            # Get parent company
            parent_company_ids = list(self.graph.predecessors(node_id))
            if parent_company_ids:
                parent_label = self.graph.nodes[parent_company_ids[0]].get('label')
                result += f"\nParent Company: {parent_label}\n"

                # Show sibling brands (other brands owned by same company)
                parent_id = parent_company_ids[0]
                sibling_ids = [b for b in self.graph.successors(parent_id) if b != node_id]
                if sibling_ids:
                    result += f"\nSibling Brands ({len(sibling_ids)}):\n"
                    sibling_labels = [self.graph.nodes[sid].get('label') for sid in sibling_ids]
                    for sibling_label in sorted(sibling_labels):
                        result += f"  - {sibling_label}\n"
            else:
                result += "\nNo parent company registered.\n"

        return result



    def get_graph_stats(self) -> str:
        # Function to display STATISTICS about the graph
        # For fun and for testing purposes
        companies = [n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'Company']
        brands = [n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'Brand']

        result = "=== GRAPH STATISTICS ===\n"
        result += f"Total Companies: {len(companies)}\n"
        result += f"Total Brands: {len(brands)}\n"
        result += f"Total Edges: {self.graph.number_of_edges()}\n"

        # Find company with most brands
        if companies:
            max_brands = max(companies, key=lambda c: self.graph.out_degree(c))
            max_label = self.graph.nodes[max_brands].get('label')
            result += f"\nLargest Portfolio: {max_label} "
            result += f"({self.graph.out_degree(max_brands)} brands)\n"

        return result


    def export_graph(self, filename: str = "brand_graph.gexf"):
        # Export graph to GEXF to put back into Gephi
        nx.write_gexf(self.graph, filename)
        return f"Graph exported to {filename}"



    def display_all(self) -> str:
        """Display the entire graph"""
        companies = [(n, attrs.get('label')) for n, attrs in self.graph.nodes(data=True)
                     if attrs.get('type') == 'Company']

        if not companies:
            return "Graph is empty."

        result = "=== BRAND OWNERSHIP GRAPH ===\n"
        for company_id, company_label in sorted(companies, key=lambda x: x[1]):
            brand_ids = list(self.graph.successors(company_id))
            result += f"\n{company_label}:\n"
            if brand_ids:
                brand_labels = [self.graph.nodes[bid].get('label') for bid in brand_ids]
                for brand_label in sorted(brand_labels):
                    result += f"  └─ {brand_label}\n"
            else:
                result += "  (no brands)\n"

        return result



if __name__ == "__main__":
    # Create the graph
    graph = BrandGraph(FileName="Graphs/testGraph.gexf")

    # Print Stats
    print(graph.get_graph_stats())

    # Display the full graph
    print(graph.display_all())
    print("\n" + "=" * 50 + "\n")

    # Query examples
    print(graph.query("PepsiCo"))
    print(graph.query("Doritos"))

