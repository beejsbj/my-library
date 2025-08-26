#VERSION: 1.00
#AUTHORS: Assistant
#LICENSING INFORMATION: Public Domain

import json
import urllib.parse
from helpers import retrieve_url
from novaprinter import prettyPrinter

class mam(object):
    """
    MyAnonaMouse (MAM) search plugin for qBittorrent
    
    Note: This plugin requires a valid MAM account and session cookie.
    You need to manually add your session cookie to the code or 
    configure it through qBittorrent's cookie management.
    """
    
    url = 'https://www.myanonamouse.net'
    name = 'MyAnonaMouse'
    supported_categories = {
        'all': ['0'],
        'books': ['14'],  # E-Books
        'music': ['15'],  # Musicology
        'software': ['0'], # MAM doesn't have software, search all
        'movies': ['0'],   # MAM doesn't have movies, search all
        'tv': ['16'],     # Radio (closest match)
        'anime': ['0'],   # MAM doesn't have anime, search all
        'games': ['0'],   # MAM doesn't have games, search all
        'pictures': ['0'] # MAM doesn't have pictures, search all
    }

    def __init__(self):
        """Initialize the MAM search plugin"""
        # You would need to set your MAM session cookie here
        # This is just a placeholder - in practice, you'd need to handle authentication
        self.session_cookie = None

    def search(self, what, cat='all'):
        """
        Search MAM using their JSON API
        
        Args:
            what: Search query string (already URL encoded)
            cat: Category to search in
        """
        try:
            # Decode the search query
            search_term = urllib.parse.unquote_plus(what)
            
            # Get the appropriate categories for MAM
            categories = self.supported_categories.get(cat, ['0'])
            
            # Build the search parameters
            search_params = {
                'tor': {
                    'text': search_term,
                    'srchIn': ['title', 'author', 'narrator', 'series'],
                    'searchType': 'all',
                    'searchIn': 'torrents',
                    'cat': categories,
                    'browseFlagsHideVsShow': '0',
                    'startDate': '',
                    'endDate': '',
                    'hash': '',
                    'sortType': 'seedersDesc',  # Sort by seeders descending
                    'startNumber': '0'
                },
                'thumbnail': 'false'
            }
            
            # Convert to JSON
            json_data = json.dumps(search_params)
            
            # Prepare the request URL
            search_url = f"{self.url}/tor/js/loadSearchJSONbasic.php"
            
            # Headers for the request
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'qBittorrent MAM Plugin'
            }
            
            # Note: In a real implementation, you'd need to handle authentication
            # This is a simplified version that would need session management
            
            # Make multiple requests to get more results (pagination)
            max_pages = 3  # Limit to first 3 pages
            results_per_page = 100
            
            for page in range(max_pages):
                search_params['tor']['startNumber'] = str(page * results_per_page)
                json_data = json.dumps(search_params)
                
                try:
                    # This would need proper authentication in practice
                    response_data = retrieve_url(search_url, json_data, headers)
                    
                    if not response_data:
                        continue
                        
                    # Parse JSON response
                    results = json.loads(response_data)
                    
                    if 'data' not in results or not results['data']:
                        break
                    
                    # Process each result
                    for torrent in results['data']:
                        self._process_result(torrent)
                        
                    # If we got fewer results than requested, we've reached the end
                    if len(results['data']) < results_per_page:
                        break
                        
                except Exception as e:
                    # Print error to stderr, not stdout
                    print(f"Error processing page {page}: {str(e)}", file=sys.stderr)
                    continue
                    
        except Exception as e:
            # Print error to stderr, not stdout
            import sys
            print(f"MAM search error: {str(e)}", file=sys.stderr)

    def _process_result(self, torrent):
        """
        Process a single torrent result and format it for qBittorrent
        
        Args:
            torrent: Dictionary containing torrent data from MAM API
        """
        try:
            # Extract torrent information
            torrent_id = torrent.get('id', '')
            title = torrent.get('title', '').strip()
            size_bytes = int(torrent.get('size', 0))
            seeders = torrent.get('seeders', 0)
            leechers = torrent.get('leechers', 0)
            
            # Convert size from bytes to human readable format
            size_str = self._format_size(size_bytes)
            
            # Build download link
            dl_hash = torrent.get('dl', '')
            if dl_hash:
                download_link = f"{self.url}/tor/download.php/{dl_hash}"
            else:
                download_link = f"{self.url}/tor/download.php?tid={torrent_id}"
            
            # Description link
            desc_link = f"{self.url}/t/{torrent_id}"
            
            # Publication date (convert from datetime string to unix timestamp)
            pub_date = torrent.get('added', '')
            pub_timestamp = self._parse_date(pub_date)
            
            # Create result dictionary
            result = {
                'link': download_link,
                'name': title,
                'size': size_str,
                'seeds': str(seeders),
                'leech': str(leechers),
                'engine_url': self.url,
                'desc_link': desc_link,
                'pub_date': str(pub_timestamp)
            }
            
            # Print the result
            prettyPrinter(result)
            
        except Exception as e:
            import sys
            print(f"Error processing torrent result: {str(e)}", file=sys.stderr)

    def _format_size(self, size_bytes):
        """Convert size in bytes to human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"

    def _parse_date(self, date_string):
        """Convert MAM date format to unix timestamp"""
        try:
            if not date_string:
                return -1
            
            # MAM returns dates in format like "2023-12-01 15:30:45"
            from datetime import datetime
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return int(dt.timestamp())
        except:
            return -1

    def download_torrent(self, info):
        """
        Download torrent file
        Note: This would require proper session management for MAM
        """
        try:
            from helpers import download_file
            print(download_file(info))
        except Exception as e:
            import sys
            print(f"Download error: {str(e)}", file=sys.stderr)
