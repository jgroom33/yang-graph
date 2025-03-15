#!/bin/bash
export PYANG_PLUGINPATH=/home/jgroom/src/yang-graph/pyang-plugin

saos10_yangs=(
  ciena-mef-fp
  ciena-mef-classifier
  ciena-mef-fd
  ciena-mef-logical-port
)

network_os=saos10
yang_dir="yangs/$network_os"
output_dir="graphs"
full_graph="graph.json"

# Ensure directories exist
if [ ! -d "$yang_dir" ]; then
  echo "Error: Directory $yang_dir does not exist."
  exit 1
fi
mkdir -p "$output_dir" || {
  echo "Error: Cannot create $output_dir"
  exit 1
}

# Generate per-module JSON files
for yang in "${saos10_yangs[@]}"; do
  yang_file="$yang_dir/$yang.yang"
  output_file="$output_dir/$yang.json"
  if [ -f "$yang_file" ]; then
    echo "Processing $yang_file..."
    pyang -f yang-graph-single -p "$yang_dir" "$yang_file" >"$output_file" 2>"logs/error_$yang.log"
    if [ $? -ne 0 ]; then
      echo "Error processing $yang_file. See logs/error_$yang.log"
      cat "error_$yang.log"
    else
      echo "Generated $output_file"
    fi
  else
    echo "Warning: $yang_file not found, skipping."
  fi
done

# Merge all JSON files into a single graph
echo "Merging graphs into $full_graph..."
python3 merge_graphs.py "$output_dir" "$full_graph"
if [ $? -ne 0 ]; then
  echo "Error merging graphs."
  exit 1
fi

echo "Complete! Graph is in $full_graph"
