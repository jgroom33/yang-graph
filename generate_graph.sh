#!/bin/bash

# Set the PYANG_PLUGINPATH, defaulting to the current script directory if not provided
PYANG_PLUGINPATH=${PYANG_PLUGINPATH:-$(dirname "$0")/pyang-plugin}
export PYANG_PLUGINPATH

saos10_yangs=(
  ciena-bgp
  ciena-cfm
  ciena-dhcpv6-client
  ciena-evpn
  ciena-flexe
  ciena-ietf-te
  ciena-igmp-snooping
  ciena-isis
  ciena-itut-g8032-draft
  ciena-l2vpn
  ciena-ldp
  ciena-mef-access-flow
  ciena-mef-classifier
  ciena-mef-cos-to-frame-map
  ciena-mef-egress-qos
  ciena-mef-fd
  ciena-mef-flood-containment-profile
  ciena-mef-fp
  ciena-mef-l2cp-profile
  ciena-mef-logical-port
  ciena-mef-meter-profile
  ciena-mef-pfg-profile
  ciena-mpls
  # ciena-openconfig-interfaces  # Empty
  ciena-ospf
  ciena-ospfv3
  ciena-packet-otn-port
  ciena-packet-ptp
  ciena-packet-xcvr
  ciena-platform
  ciena-rib
  ciena-routing-policy
  ciena-sat
  ciena-sr
  ciena-sr-policy
  ciena-sync
  # ciena-system          # Empty
  ciena-vrf
  ietf-interfaces
  ietf-pseudowires
  ietf-snmp
  ietf-twamp
  mef-cfm
  openconfig-interfaces
  openconfig-system
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
mkdir -p "logs" || {
  echo "Error: Cannot create logs directory"
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
python3 merge_graphs.py "$output_dir" "docs/$full_graph"
if [ $? -ne 0 ]; then
  echo "Error merging graphs."
  exit 1
fi

echo "Complete! Graph is in $full_graph"
