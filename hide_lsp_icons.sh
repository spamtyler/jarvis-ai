#!/bin/bash

# Directory for user-specific desktop entries
USER_APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$USER_APPS_DIR"

echo "Hiding LSP plugins..."

# Find all LSP desktop files in /usr/share/applications
find /usr/share/applications -name "*lsp_plug*" | while read -r file; do
    filename=$(basename "$file")
    target="$USER_APPS_DIR/$filename"
    
    # Copy the file to the user's directory
    cp "$file" "$target"
    
    # Add NoDisplay=true to the end of the file
    if ! grep -q "NoDisplay=true" "$target"; then
        echo "NoDisplay=true" >> "$target"
        echo "Hidden: $filename"
    else
        echo "Already hidden: $filename"
    fi
done

echo "Updating desktop database..."
update-desktop-database "$USER_APPS_DIR"
echo "Done."
