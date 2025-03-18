#!/usr/bin/env python3

import json
import os
import argparse
import logging

logging.basicConfig(level=logging.INFO)


def merge_graphs(input_dir, output_file, cytoscape_format=True):
    all_nodes = {}
    all_edges = []

    # Load all JSON files from the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(input_dir, filename)
            logging.info(f"Loading {filepath}")
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    for node in data.get("nodes", []):
                        all_nodes[node["id"]] = node
                    all_edges.extend(data.get("edges", []))
            except Exception as e:
                logging.error(f"Error loading {filepath}: {e}")

    # Filter edges: require source to be a node, but allow target to be any reference
    valid_edges = []
    dropped_edges = []
    placeholder_nodes = {}
    for edge in all_edges:
        if edge["source"] in all_nodes:
            if edge["target"] in all_nodes:
                valid_edges.append(edge)
            else:
                logging.warning(f"Target node {edge['target']} not found for edge {edge}")
                # Add placeholder node for missing target
                if edge["target"] not in placeholder_nodes:
                    placeholder_nodes[edge["target"]] = {
                        "id": edge["target"],
                        "type": "unknown",
                        "module": edge["target"].split(":")[0] if ":" in edge["target"] else "unknown",
                        "description": "Referenced but not defined in processed YANG modules",
                        "key": None,
                        "isPlaceholder": True,
                    }
                valid_edges.append(edge)
        else:
            dropped_edges.append(edge)

    # Add placeholder nodes to all_nodes
    all_nodes.update(placeholder_nodes)

    logging.info(
        f"Found {len(all_nodes)} nodes and {len(valid_edges)} valid edges (out of {len(all_edges)} potential)"
    )
    if dropped_edges:
        logging.warning(
            f"Dropped {len(dropped_edges)} edges with invalid sources: {[e['source'] for e in dropped_edges[:5]]}"
        )

    # Format output
    if cytoscape_format:
        result = {
            "graph": [{"data": node} for node in all_nodes.values()]
            + [{"data": edge} for edge in valid_edges]
        }
    else:
        result = {"nodes": list(all_nodes.values()), "edges": valid_edges}

    try:
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logging.info(f"Combined graph written to {output_file}")
    except Exception as e:
        logging.error(f"Error writing output: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge per-module YANG graph JSON files into a single graph."
    )
    parser.add_argument("input_dir", help="Directory containing per-module JSON files")
    parser.add_argument("output_file", help="Output file for the combined graph")
    parser.add_argument(
        "--no-cytoscape",
        action="store_false",
        dest="cytoscape_format",
        help="Output in simple nodes/edges format instead of Cytoscape.js format",
    )
    args = parser.parse_args()

    merge_graphs(
        args.input_dir, args.output_file, cytoscape_format=args.cytoscape_format
    )
