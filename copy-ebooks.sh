#!/bin/bash
# /mnt/HC_Volume_102773441/library/scripts/copy-ebooks.sh

# Source and destination directories
DOWNLOADS_DIR="/mnt/HC_Volume_102773441/library/downloads"
INGEST_DIR="/mnt/HC_Volume_102773441/library/ingest/books"

# Create directories if they don't exist
mkdir -p "$INGEST_DIR"
mkdir -p "/mnt/HC_Volume_102773441/library/logs"

# Log file
LOG_FILE="/mnt/HC_Volume_102773441/library/logs/ebook-copier.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Find and copy ebook files
find "$DOWNLOADS_DIR" -type f \( -iname "*.epub" -o -iname "*.mobi" -o -iname "*.azw" -o -iname "*.azw3" -o -iname "*.pdf" \) -print0 | while IFS= read -r -d '' file; do
    # Skip if file is already in ingest directory
    if [[ "$file" == *"/ingest/"* ]]; then
        continue
    fi
    
    filename=$(basename "$file")
    destination="$INGEST_DIR/$filename"
    
    # Skip if file already exists in destination
    if [[ -f "$destination" ]]; then
        continue
    fi
    
    # Copy the file (keeping original for seeding)
    if cp "$file" "$destination"; then
        log_message "COPIED: $filename to ingest directory"
        echo "Copied: $filename"
    else
        log_message "ERROR: Failed to copy $filename"
    fi
done

log_message "Ebook copy scan completed"