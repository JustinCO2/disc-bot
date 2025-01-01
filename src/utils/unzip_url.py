from box import Timer, handler, ic, ib, rel2abs
import argparse
import urllib.request
import urllib.error
import zipfile
import gzip
import os
import io
import shutil
import time
import hashlib
from pathlib import Path
import sys
timer = Timer()

def get_cache_path(url: str) -> Path:
    """Get cache file path for a URL"""
    # Use system's temp dir and create our cache subdir
    cache_dir = Path(os.getenv('TEMP', '/tmp')) / 'unzip_url_cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename from URL hash
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return cache_dir / url_hash

def format_size(size_bytes: int) -> str:
    """Convert bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024

def download_with_cache(url_or_path: str) -> tuple[bytes, str]:
    """Download URL or read local file with caching (1 hour expiry for URLs)"""
    # Check if it's a local file
    if os.path.exists(url_or_path):
        try:
            data = Path(url_or_path).read_bytes()
            # Detect file type
            try:
                zipfile.ZipFile(io.BytesIO(data))
                return data, 'zip'
            except zipfile.BadZipFile:
                try:
                    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                        gz.read(1)
                    return data, 'gz'
                except OSError:
                    raise ValueError("Local file is neither a ZIP nor GZIP archive")
        except IOError as e:
            raise ValueError(f"Failed to read local file: {str(e)}")
    
    # Not a local file, treat as URL
    if not url_or_path.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https:// or be a local file path")
    
    cache_path = get_cache_path(url_or_path)
    
    # Check if we have a valid cache file
    if cache_path.exists():
        mtime = cache_path.stat().st_mtime
        if time.time() - mtime < 3600:  # 1 hour cache
            data = cache_path.read_bytes()
            # Need to detect file type for cached files too
            try:
                zipfile.ZipFile(io.BytesIO(data))
                return data, 'zip'
            except zipfile.BadZipFile:
                try:
                    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                        gz.read(1)
                    return data, 'gz'
                except OSError:
                    raise ValueError("Cached file is neither a ZIP nor GZIP archive")
    
    # Download with progress
    print(f"Downloading {url_or_path}...")
    
    try:
        with urllib.request.urlopen(url_or_path) as response:
            # Verify content type if available
            content_type = response.headers.get('content-type', '').lower()
            if content_type and not any(t in content_type for t in ['zip', 'gzip', 'octet-stream', 'binary']):
                raise ValueError(f"Unexpected content type: {content_type}")
            
            total_size = response.headers.get('content-length')
            if total_size is not None:
                total_size = int(total_size)
            
            # Download with progress updates
            data = bytearray()
            size_downloaded = 0
            chunk_size = 8192
            last_percent = -1
            
            while True:
                try:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                        
                    data.extend(chunk)
                    size_downloaded += len(chunk)
                    
                    if total_size:
                        percent = int(size_downloaded * 100 / total_size)
                        if percent != last_percent:
                            print(f"\rProgress: {percent}% ({format_size(size_downloaded)}/{format_size(total_size)})", end="", flush=True)
                            last_percent = percent
                    else:
                        print(f"\rDownloaded: {format_size(size_downloaded)}", end="", flush=True)
                except (urllib.error.URLError, ConnectionError) as e:
                    raise ConnectionError(f"Download failed: {str(e)}")
            
            print()  # New line after progress
            
            # Try to detect file type from content
            try:
                # Try zip first
                zipfile.ZipFile(io.BytesIO(data))
                file_type = 'zip'
            except zipfile.BadZipFile:
                try:
                    # Try gzip next
                    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                        gz.read(1)  # Read a byte to verify it's valid
                    file_type = 'gz'
                except OSError:
                    raise ValueError("Downloaded file is neither a ZIP nor GZIP archive")
    
    except urllib.error.HTTPError as e:
        raise ConnectionError(f"HTTP error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to reach server: {str(e.reason)}")
    except Exception as e:
        raise ConnectionError(f"Download failed: {str(e)}")
    
    # Cache the downloaded data
    cache_path.write_bytes(data)
    return data, file_type

def unzip_url(url: str, select: str | None = None, out_dir: str | None = None, rename: str | None = None):
    """
    Extract file(s) from a remote zip/gz archive, or list contents if only URL provided
    
    Args:
        url: URL pointing to a .zip or .gz file
        select: Path within archive to extract (file or folder), or None to list contents
        out_dir: Directory to extract to (required if select is provided)
        rename: Optional new name (only applies to single files)
    """
    try:
        # Download the file (with caching)
        data, file_type = download_with_cache(url)
        
        if file_type == 'zip':
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if not select:
                    # List contents with helpful message
                    print("Valid --select options:")
                    print("------------------------")
                    for info in zf.filelist:
                        if not info.filename.endswith('/'):  # Skip empty directories
                            print(info.filename)
                    return
                
                # Validate --select path exists
                files = zf.namelist()
                if select.endswith('/') or select.endswith('\\'):
                    # For directories, check if any files start with this path
                    if not any(f.startswith(select) for f in files):
                        print(f"Error: Directory '{select}' not found in archive")
                        print("\nValid --select options:")
                        print("------------------------")
                        for info in zf.filelist:
                            if not info.filename.endswith('/'):
                                print(info.filename)
                        sys.exit(1)
                else:
                    # For files, check exact match
                    if select not in files:
                        print(f"Error: File '{select}' not found in archive")
                        print("\nValid --select options:")
                        print("------------------------")
                        for info in zf.filelist:
                            if not info.filename.endswith('/'):
                                print(info.filename)
                        sys.exit(1)
                
                # If no out_dir, we're just validating
                if not out_dir:
                    return
                
                # Handle extraction
                if select.endswith('/') or select.endswith('\\'):
                    # Extract directory
                    extracted = []
                    for info in zf.filelist:
                        if info.filename.startswith(select):
                            out_path = Path(out_dir) / info.filename
                            zf.extract(info, out_dir)
                            extracted.append(out_path)
                    print(f"Extracted {len(extracted)} files to {Path(out_dir) / select}")
                else:
                    # Extract single file
                    if rename:
                        out_name = rename
                    else:
                        out_name = Path(select).name  # Just the filename, no directories
                        
                    # Extract directly to out_dir
                    with zf.open(select) as source:
                        out_path = Path(out_dir) / out_name
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(out_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        print(f"Extracted: {out_path}")
                        
        elif file_type == 'gz':
            if not select:
                # For gz, show the filename with helpful message
                print("Valid --select options:")
                print("------------------------")
                print(Path(url).stem)
                return
                
            # For gz, only '.' is valid as it contains just one file
            if select != '.' and select != Path(url).stem:
                print(f"Error: For .gz files, use --select '.' or '{Path(url).stem}'")
                print("\nValid --select options:")
                print("------------------------")
                print(Path(url).stem)
                sys.exit(1)
                
            # If no out_dir, we're just validating
            if not out_dir:
                return
                
            # gz only contains one file
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
                out_path = Path(out_dir)
                if rename:
                    out_path = out_path / rename
                else:
                    out_path = out_path / (Path(url).stem if select == '.' else select)
                    
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, 'wb') as f:
                    shutil.copyfileobj(gz, f)
                print(f"Extracted: {out_path}")
            
    except (ValueError, ConnectionError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Extract files from remote zip/gz archives')
    
    parser.add_argument('url', help='URL or path to a .zip or .gz file')
    parser.add_argument('--select', help='''Path within archive to extract. Examples:
        - Single file: "folder/file.txt" -> extracts to "output/file.txt"
        - Folder: "folder/" -> extracts to "output/folder/..." (preserves structure)
        If omitted, lists archive contents''')
    parser.add_argument('--dir', help='Directory to extract to (required with --select)')
    parser.add_argument('--rename', help='Optional new name for extracted file (only works with single file --select)')
    
    args = parser.parse_args()
    
    if args.select:
        if not args.dir:
            # Just validate the --select path and show what would be extracted
            try:
                unzip_url(args.url, args.select)
                print("\nPath exists in archive. Use --dir to specify where to extract it.")
                sys.exit(1)
            except ValueError as e:
                # If path doesn't exist, unzip_url will show valid options and error
                sys.exit(1)
        unzip_url(args.url, args.select, args.dir, args.rename)
    else:
        # Just list contents when only URL is provided
        unzip_url(args.url)

if __name__ == "__main__":
    with handler():
        main()
