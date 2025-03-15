#!/usr/bin/env python3

import json
import os
import argparse
import logging

logging.basicConfig(level=logging.INFO)


def merge_graphs(input_dir, output_file):
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
                    for node in data["nodes"]:
                        all_nodes[node["id"]] = node
                    all_edges.extend(data["edges"])
            except Exception as e:
                logging.error(f"Error loading {filepath}: {e}")

    # Filter edges to only those with valid source and target nodes
    valid_edges = [
        edge
        for edge in all_edges
        if edge["source"] in all_nodes and edge["target"] in all_nodes
    ]
    logging.info(
        f"Found {len(all_nodes)} nodes and {len(valid_edges)} valid edges (out of {len(all_edges)} potential)"
    )

    # Format output for Cytoscape.js
    result = {
        "graph": [{"data": node} for node in all_nodes.values()]
        + [{"data": edge} for edge in valid_edges]
    }

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
    args = parser.parse_args()

    merge_graphs(args.input_dir, args.output_file)
