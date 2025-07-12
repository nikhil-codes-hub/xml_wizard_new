#!/bin/bash

# Clear POC Results Script
# Deletes ONLY JSON files from enhanced_exploration subdirectory
# Preserves manual_mapping_analysis.json and other important files

echo "🧹 Clearing Enhanced Exploration POC Results..."
echo "================================================"

# Define the specific enhanced_exploration directory
ENHANCED_EXPLORATION_DIR="/home/sidd/dev/xml_wizard/agentic_test_gen/poc_results/enhanced_exploration"

# Check if directory exists
if [ ! -d "$ENHANCED_EXPLORATION_DIR" ]; then
    echo "❌ ERROR: enhanced_exploration directory not found at $ENHANCED_EXPLORATION_DIR"
    echo "ℹ️  Creating directory for POC results..."
    mkdir -p "$ENHANCED_EXPLORATION_DIR"
fi

# Count files before deletion
TOTAL_FILES=$(find "$ENHANCED_EXPLORATION_DIR" -name "*.json" -type f | wc -l)

if [ "$TOTAL_FILES" -eq 0 ]; then
    echo "✅ No JSON files found in enhanced_exploration - directory is already clean"
    exit 0
fi

echo "📄 Found $TOTAL_FILES JSON files to delete from enhanced_exploration"
echo "🔒 Preserving manual_mapping_analysis.json and other files outside enhanced_exploration"

# Delete JSON files ONLY from enhanced_exploration directory
find "$ENHANCED_EXPLORATION_DIR" -name "*.json" -type f -delete

# Verify deletion
REMAINING_FILES=$(find "$ENHANCED_EXPLORATION_DIR" -name "*.json" -type f | wc -l)

if [ "$REMAINING_FILES" -eq 0 ]; then
    echo "✅ Successfully deleted $TOTAL_FILES JSON files from enhanced_exploration"
    echo "🎯 Enhanced exploration directory is now clean for fresh POC run"
    echo "🔒 Manual mapping analysis and other files preserved"
else
    echo "⚠️  Warning: $REMAINING_FILES JSON files remain in enhanced_exploration"
fi

echo "================================================"
echo "Ready to run: python xslt_mapping_extractor_poc.py"