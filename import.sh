#!/bin/bash

# Check if a parameter was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <zipfile>"
    exit 1
fi

ZIP_FILE="$1"

# Check if the zip file exists
if [ ! -f "$ZIP_FILE" ]; then
    echo "Error: File '$ZIP_FILE' not found"
    exit 1
fi

# Create a temporary directory for extraction
TEMP_DIR=$(mktemp -d)

# Check if temp directory was created successfully
if [ ! -d "$TEMP_DIR" ]; then
    echo "Error: Failed to create temporary directory"
    exit 1
fi

# Extract the zip file to the temporary directory
if ! unzip -q "$ZIP_FILE" -d "$TEMP_DIR"; then
    echo "Error: Failed to extract zip file"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Check if the data directory exists in the extracted contents
if [ ! -d "$TEMP_DIR/data" ]; then
    echo "Error: No 'data' directory found in zip file"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Copy contents of the data directory to current directory
if ! cp -r "$TEMP_DIR/data/"* ./data/; then
    echo "Error: Failed to copy files"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo "Successfully extracted contents of data directory from $ZIP_FILE"

python3 import_data.py