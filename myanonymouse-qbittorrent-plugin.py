# VERSION: 1.00
# AUTHORS: Your Name (your.email@example.com)

# LICENSING INFORMATION
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

import json
import urllib.parse
import urllib.request
import sys
from helpers import retrieve_url, download_file
from novaprinter import prettyPrinter

class myanonymouse(object):
    """
    MyAnonamouse search engine plugin for qBittorrent
    """
    url = 'https://www.myanonamouse.net'
    name = 'MyAnonamouse'
    supported_categories = {
        'all': '0',
        'books': '14',  # E-Books
        'audio': '13'   # AudioBooks
    }
    
    # REQUIRED: Configure these with your MAM credentials
    # You need to get these from your MAM account settings
    USERNAME = ""  # Your MAM username
    PASSWORD = ""  # Your MAM password
    # Alternative: Use session cookies instead
    COOKIES = ""   # Your browser cookies for MAM (format: "name1=value1; name2=value2")
    
    def download_torrent(self, info):
        """
        Download torrent file. This handles MAM's authentication requirements.
        """
        try:
            print(download_file(info), file=sys.stderr)
        except Exception as e:
            print(f"Download error: {str(e)}", file=sys.stderr)
    
    def search(self, what, cat='all'):
        """
        Search for torrents on MyAnonamouse using their JSON API
        """
        if not self.USERNAME or not self.PASSWORD:
            print("ERROR: Please configure USERNAME and PASSWORD in the plugin file", file=sys.stderr)
            return
            
        try:
            # Map qBittorrent categories to MAM categories
            mam_cat = self.supported_categories.get(cat, '0')
            
            # Prepare search parameters based on MAM's API documentation
            search_params = {
                "tor": {
                    "text": what,
                    "srchIn": ["title", "author", "narrator"],
                    "searchType": "all",
                    "searchIn": "torrents",
                    "cat": [mam_cat],
                    "browseFlagsHideVsShow": "0",
                    "startDate": "",
                    "endDate": "",
                    "hash": "",
                    "sortType": "seedersDesc",  # Sort by seeders (most seeds first)
                    "startNumber": "0"
                },
                "thumbnail": "true"
            }
            
            # Convert to JSON
            json_data = json.dumps(search_params)
            
            # Search URL from MAM API documentation
            search_url = f"{self.url}/tor/js/loadSearchJSONbasic.php"
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'qBittorrent Search Plugin'
            }
            
            # Add cookies if provided (recommended method for MAM)
            if self.COOKIES:
                headers['Cookie'] = self.COOKIES
            elif self.USERNAME and self.PASSWORD:
                # Basic auth fallback (may not work with MAM)
                import base64
                credentials = f"{self.USERNAME}:{self.PASSWORD}"
                encoded_credentials = base64.b64encode(credentials.encode('ascii')).decode('ascii')
                headers['Authorization'] = f'Basic {encoded_credentials}'
            
            # Make the request using qBittorrent's helper
            response_data = retrieve_url(search_url, json_data.encode('utf-8'), headers)
            
            # Parse JSON response
            data = json.loads(response_data)
            
            # Process results
            if 'data' in data and isinstance(data['data'], list):
                for torrent in data['data']:
                    self.parse_and_print_result(torrent)
            else:
                print("No results found or invalid response format", file=sys.stderr)
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}", file=sys.stderr)
        except Exception as e:
            print(f"Search error: {str(e)}", file=sys.stderr)
    
    def parse_and_print_result(self, torrent):
        """
        Parse individual torrent result from MAM API and print using prettyPrinter
        """
        try:
            # Extract data from the API response according to MAM API docs
            torrent_id = str(torrent.get('id', ''))
            title = torrent.get('title', torrent.get('name', 'Unknown Title'))
            size_bytes = torrent.get('size', '0')
            seeders = str(torrent.get('seeders', '-1'))
            leechers = str(torrent.get('leechers', '-1'))
            
            # Create download link using MAM's download hash
            dl_hash = torrent.get('dl', '')
            if dl_hash:
                download_link = f"{self.url}/tor/download.php/{dl_hash}"
            else:
                download_link = f"{self.url}/tor/download.php?tid={torrent_id}"
            
            # Create description link
            desc_link = f"{self.url}/t/{torrent_id}"
            
            # Convert size from bytes to human readable format
            size_str = self.format_size_bytes(size_bytes)
            
            # Add author information to title if available
            author_info = torrent.get('author_info', '')
            if author_info:
                try:
                    authors = json.loads(author_info)
                    if authors:
                        author_names = list(authors.values())[:2]  # First 2 authors
                        if author_names:
                            title += f" - {', '.join(author_names)}"
                except:
                    pass  # Skip if author parsing fails
            
            # Get publication date (MAM provides 'added' field)
            pub_date = str(torrent.get('added', '-1'))
            if pub_date and pub_date != '-1':
                try:
                    # Convert MAM datetime to unix timestamp if needed
                    # MAM format might be "2023-01-15 12:30:45" - you may need to adjust this
                    import time
                    import datetime
                    if 'T' in pub_date or '-' in pub_date:
                        # Parse ISO format or similar
                        dt = datetime.datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        pub_date = str(int(dt.timestamp()))
                except:
                    pub_date = '-1'
            
            # Create result dictionary for prettyPrinter
            result = {
                'link': download_link,
                'name': title,
                'size': size_str,
                'seeds': seeders,
                'leech': leechers,
                'engine_url': self.url,
                'desc_link': desc_link,
                'pub_date': pub_date
            }
            
            # Print result using qBittorrent's format
            prettyPrinter(result)
            
        except Exception as e:
            # Don't print errors for individual results to avoid spam
            print(f"Error parsing result: {str(e)}", file=sys.stderr)
    
    def format_size_bytes(self, size_bytes):
        """
        Convert bytes to human readable format
        """
        try:
            size_num = int(size_bytes) if str(size_bytes).isdigit() else 0
            if size_num == 0:
                return "0 B"
            
            size_names = ["B", "KB", "MB", "GB", "TB"]
            import math
            i = int(math.floor(math.log(size_num, 1024)))
            p = math.pow(1024, i)
            s = round(size_num / p, 2)
            return f"{s} {size_names[i]}"
        except:
            return str(size_bytes)


# Required function for qBittorrent - DO NOT CHANGE name or parameters
def search(what, cat='all'):
    """
    Entry point called by qBittorrent
    """
    engine = myanonymouse()
    engine.search(what, cat)