#\!/bin/bash

# Cleanup script for XML Wizard temporary directories
# This script removes temporary directories created during the infinite loop issue

echo "XML Wizard Temp Directory Cleanup"
echo "=================================="

# Find all temp directories starting with tmp in /tmp
TEMP_DIRS=$(find /tmp -maxdepth 1 -type d -name "tmp*" 2>/dev/null)

if [ -z "$TEMP_DIRS" ]; then
    echo "No temporary directories found in /tmp"
    exit 0
fi

# Count directories
DIR_COUNT=$(echo "$TEMP_DIRS"  < /dev/null |  wc -l)
echo "Found $DIR_COUNT temporary directories:"
echo

# Show what will be deleted
echo "$TEMP_DIRS" | while read dir; do
    if [ -d "$dir" ]; then
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "  $dir ($SIZE)"
    fi
done

echo
echo "WARNING: This will delete all temporary directories in /tmp starting with 'tmp'"

# Ask for confirmation
read -p "Are you sure you want to delete these directories? [y/N]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting temporary directories..."
    
    # Delete each directory
    echo "$TEMP_DIRS" | while read dir; do
        if [ -d "$dir" ]; then
            echo "Removing: $dir"
            rm -rf "$dir"
        fi
    done
    
    echo "Cleanup completed\!"
else
    echo "Cleanup cancelled."
fi
