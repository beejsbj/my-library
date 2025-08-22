# Ebook Auto-Copy Setup Instructions

## Files Created
- `copy-ebooks.sh` - The main script that copies ebook files from downloads to ingest

## Installation Steps

### 1. Upload Script to Server
Copy the `copy-ebooks.sh` file to your Coolify server:

```bash
# Create the scripts directory
mkdir -p /mnt/HC_Volume_102773441/library/scripts

# Copy the script (upload via SCP, SFTP, or copy-paste)
cp copy-ebooks.sh /mnt/HC_Volume_102773441/library/scripts/copy-ebooks.sh

# Make it executable
chmod +x /mnt/HC_Volume_102773441/library/scripts/copy-ebooks.sh
```

### 2. Set Up Automatic Execution
Add to system crontab to run every 10 minutes:

```bash
# Edit system crontab
sudo crontab -e

# Add this line:
*/10 * * * * /mnt/HC_Volume_102773441/library/scripts/copy-ebooks.sh >/dev/null 2>&1
```

### 3. Configure qBittorrent for Auto-Delete
In qBittorrent Web UI:
1. Go to **Tools > Options > BitTorrent**
2. Enable **"Remove torrent when seeding time reaches"**
3. Set to **4320 minutes** (3 days)
4. Choose **"Remove torrent and its files"**

### 4. Update Docker Compose (if needed)
Ensure your booklore service has the correct ingest path:

```yaml
booklore:
  volumes:
    - '/mnt/HC_Volume_102773441/library/data/booklore:/app/data'
    - '/mnt/HC_Volume_102773441/library/media/books:/books'
    - '/mnt/HC_Volume_102773441/library/ingest/books:/bookdrop'
```

## How It Works
1. **Every 10 minutes**: Script scans downloads folder
2. **Finds new ebooks**: Copies them to ingest folder (keeps originals)
3. **Booklore processes them**: Automatically adds to library
4. **qBittorrent keeps seeding**: Original files stay for 3 days
5. **Auto-cleanup**: qBittorrent deletes after 3 days

## Monitoring
Check the log file for activity:
```bash
tail -f /mnt/HC_Volume_102773441/library/logs/ebook-copier.log
```

## Supported File Types
- `.epub`
- `.mobi` 
- `.azw`
- `.azw3`
- `.pdf`