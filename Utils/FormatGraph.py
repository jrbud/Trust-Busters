import csv
from typing import Dict, Set, List, Tuple


def Formatter(InFilename: str, NodesFile: str = "Nodes.csv", EdgesFile: str = "Edges.csv"):

    # Dictionary of Node Labels to Types (Company/Brand
    nodes: Dict[str, str] = {}  # {label: type}
    edges: List[Tuple[str, str]] = []  # [(company, brand)]

    # Read the input CSV
    print(f"Reading {InFilename}...")
    with open(InFilename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        # Check if formatting is good
        if 'Company' not in reader.fieldnames or 'Brand' not in reader.fieldnames:
            raise ValueError("Improper Formatting: Input CSV must have 'Company' and 'Brand' columns")

        for row in reader:
            company = row['Company'].strip()
            brand = row['Brand'].strip()

            # Skip empty rows
            if not company or not brand:
                continue

            # Add nodes (only if not already added)
            if company not in nodes:
                nodes[company] = 'Company'
            if brand not in nodes:
                nodes[brand] = 'Brand'

            # Add edge (company -> brand)
            edges.append((company, brand))

    print(f"Found {len(nodes)} unique nodes and {len(edges)} edges")

    # Create integer Ids for all nodes
    # Dictionary of Node Label to Id
    label_to_id: Dict[str, int] = {}
    for idx, label in enumerate(sorted(nodes.keys()), start=1):
        label_to_id[label] = idx

    # Write Nodes CSV
    print(f"Writing {NodesFile}...")
    with open(NodesFile, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Id', 'Label', 'type'])

        for label in sorted(nodes.keys()):
            node_id = label_to_id[label]
            node_type = nodes[label]
            writer.writerow([node_id, label, node_type])

    # Write Edges CSV
    print(f"Writing {EdgesFile}...")
    with open(EdgesFile, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Source', 'Target'])

        for company, brand in edges:
            source_id = label_to_id[company]
            target_id = label_to_id[brand]
            writer.writerow([source_id, target_id])

    # Print summary
    print("\n=== CONVERSION SUMMARY ===")
    print(f"Total Nodes: {len(nodes)}")
    print(f"  - Companies: {sum(1 for t in nodes.values() if t == 'Company')}")
    print(f"  - Brands: {sum(1 for t in nodes.values() if t == 'Brand')}")
    print(f"Total Edges: {len(edges)}")
    print(f"\nFiles created:")
    print(f"  - {NodesFile}")
    print(f"  - {EdgesFile}")

    return label_to_id, nodes, edges


def validate_graph(nodes_file: str, edges_file: str):
    #Check that output files are well formatted !!
    print("\n=== VALIDATING OUTPUT ===")

    # Read nodes
    node_ids = set()
    with open(nodes_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_ids.add(int(row['Id']))

    print(f"Nodes file: {len(node_ids)} unique IDs found")

    # Read and validate edges
    edge_count = 0
    invalid_edges = []
    with open(edges_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            edge_count += 1
            source = int(row['Source'])
            target = int(row['Target'])

            # Check if IDs exist in nodes
            if source not in node_ids:
                invalid_edges.append(f"Source ID {source} not found in nodes")
            if target not in node_ids:
                invalid_edges.append(f"Target ID {target} not found in nodes")

    print(f"Edges file: {edge_count} edges found")

    if invalid_edges:
        print(f"\n⚠️  WARNING: Found {len(invalid_edges)} invalid edge(s):")
        for error in invalid_edges[:5]:  # Show first 5
            print(f"  - {error}")
    else:
        print("✓ All edges reference valid node IDs")

    print("\nValidation complete!")


if __name__ == "__main__":
    # Example: Create a sample input CSV for testing
    sample_data = """Company,Brand
PepsiCo,Doritos
PepsiCo,Lay's
PepsiCo,Mountain Dew
PepsiCo,Pepsi
Mondelez,Oreo
Mondelez,Cadbury
Mondelez,Trident
Procter & Gamble,Tide
Procter & Gamble,Crest
Procter & Gamble,Gillette"""

    # Write sample input
    with open("Files/sample_input.csv", 'w') as f:
        f.write(sample_data)


    # Convert the CSV
    try:
        Formatter(InFilename="Files/sample_input.csv", NodesFile="Files/Nodes.csv", EdgesFile="Files/Edges.csv")

        # Validate the output
        validate_graph("Files/Nodes.csv", "Files/Edges.csv")

        # Show sample output
        print("\n=== SAMPLE OUTPUT ===")
        print("\nNodes.csv (first 5 rows):")
        with open("Files/Nodes.csv", 'r') as f:
            for i, line in enumerate(f):
                if i < 6:  # Header + 5 rows
                    print(f"  {line.strip()}")

        print("\nEdges.csv (first 5 rows):")
        with open("Files/Edges.csv", 'r') as f:
            for i, line in enumerate(f):
                if i < 6:  # Header + 5 rows
                    print(f"  {line.strip()}")

    except Exception as e:
        print(f"Error: {e}")
