#!/bin/bash

# Set the PYANG_PLUGINPATH, defaulting to the current script directory if not provided
PYANG_PLUGINPATH=${PYANG_PLUGINPATH:-$(dirname "$0")/pyang-plugin}
export PYANG_PLUGINPATH

# Function to process YANG files for a given network OS
process_yang_files() {
  local network_os="$1"
  shift
  local yangs=("$@")
  local yang_dir="yangs/$network_os"
  local output_dir="graphs/$network_os"

  # Ensure directories exist
  if [ ! -d "$yang_dir" ]; then
    echo "Error: Directory $yang_dir does not exist."
    return 1
  fi
  mkdir -p "$output_dir" || {
    echo "Error: Cannot create $output_dir"
    return 1
  }
  mkdir -p "logs" || {
    echo "Error: Cannot create logs directory"
    return 1
  }

  # Generate per-module JSON files
  for yang in "${yangs[@]}"; do
    yang_file="$yang_dir/$yang.yang"
    output_file="$output_dir/$yang.json"
    if [ -f "$yang_file" ]; then
      echo "Processing $yang_file..."
      pyang -f yang-graph-single -p "$yang_dir" "$yang_file" >"$output_file" 2>"logs/error_$yang.log"
      if [ $? -ne 0 ]; then
        echo "Error processing $yang_file. See logs/error_$yang.log"
        cat "logs/error_$yang.log"
      else
        echo "Generated $output_file"
      fi
    else
      echo "Warning: $yang_file not found, skipping."
    fi
  done

  # Merge all JSON files into a single graph
  echo "Merging graphs into graph.json..."
  python3 merge_graphs.py "$output_dir" "docs/graphs/$network_os/graph.json"
  if [ $? -ne 0 ]; then
    echo "Error merging graphs."
    return 1
  fi

  echo "Complete! Graph is in docs/graphs/$network_os/graph.json"
  return 0
}

# SAOS10 YANG models
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

# Waveserver AI YANG models
waveserver_yangs=(
  ciena-waveserver-aaa
  ciena-waveserver-application-auto-fiber-discovery
  ciena-waveserver-application-otdr
  ciena-waveserver-chassis
  ciena-waveserver-configuration
  ciena-waveserver-interfaces
  ciena-waveserver-license
  ciena-waveserver-lldp
  ciena-waveserver-module
  ciena-waveserver-ndp
  ciena-waveserver-pkix
  ciena-waveserver-pm
  ciena-waveserver-pm-tca
  ciena-waveserver-port
  ciena-waveserver-protection
  ciena-waveserver-ptp
  ciena-waveserver-snmp
  ciena-waveserver-software
  ciena-waveserver-spli
  ciena-waveserver-system
  ciena-waveserver-xcvr
)

# Process both sets of YANG files
process_yang_files "saos10" "${saos10_yangs[@]}"
process_yang_files "waveserverai" "${waveserver_yangs[@]}"
