import pytest
from pathlib import Path
import zipfile
import io
import subprocess
import os
import shutil

@pytest.fixture
def archive_path(tmp_path):
    """Create a test zip archive with known contents"""
    archive_path = tmp_path / "archive.zip"
    
    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zf:
        # Add a file in root
        zf.writestr('ABOUT', 'About this archive')
        # Add files in subdirectory
        zf.writestr('local/file.txt', 'This is a test file')
        zf.writestr('local/another.txt', 'Another test file')
        zf.writestr('local/subdir/nested.txt', 'Nested test file')
    
    # Write the zip to disk
    archive_path.write_bytes(zip_buffer.getvalue())
    return archive_path

def test_list_contents(archive_path):
    """List archive contents"""
    print(f"\n$ python src/utils/unzip_url.py {archive_path}")
    result = subprocess.run(['python', 'src/utils/unzip_url.py', str(archive_path)], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    assert 'ABOUT' in result.stdout
    assert 'local/file.txt' in result.stdout

def test_invalid_select(archive_path):
    """Test invalid --select option"""
    print(f"\n$ python src/utils/unzip_url.py {archive_path} --select missing.txt")
    result = subprocess.run(['python', 'src/utils/unzip_url.py', str(archive_path), 
                           '--select', 'missing.txt'], 
                          capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Error: File' in result.stdout
    assert 'ABOUT' in result.stdout
    assert 'local/file.txt' in result.stdout

def test_valid_select_without_dir(archive_path):
    """Test --select without --dir"""
    print(f"\n$ python src/utils/unzip_url.py {archive_path} --select ABOUT")
    result = subprocess.run(['python', 'src/utils/unzip_url.py', str(archive_path),
                           '--select', 'ABOUT'],
                          capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Path exists in archive' in result.stdout
    assert '--dir' in result.stdout

def test_extract_nested_file(archive_path, tmp_path):
    """Extract single nested file"""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    print(f"\n$ python src/utils/unzip_url.py {archive_path} --select local/file.txt --dir {out_dir}")
    
    result = subprocess.run(['python', 'src/utils/unzip_url.py', str(archive_path),
                           '--select', 'local/file.txt',
                           '--dir', str(out_dir)],
                          capture_output=True, text=True)
    
    assert result.returncode == 0
    assert (out_dir / 'file.txt').exists()
    assert (out_dir / 'file.txt').read_text() == 'This is a test file'

def test_extract_with_rename(archive_path, tmp_path):
    """Extract file with --rename"""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    print(f"\n$ python src/utils/unzip_url.py {archive_path} --select ABOUT --dir {out_dir} --rename info.txt")
    
    result = subprocess.run(['python', 'src/utils/unzip_url.py', str(archive_path),
                           '--select', 'ABOUT',
                           '--dir', str(out_dir),
                           '--rename', 'info.txt'],
                          capture_output=True, text=True)
    
    assert result.returncode == 0
    assert (out_dir / 'info.txt').exists()
    assert (out_dir / 'info.txt').read_text() == 'About this archive'

def test_extract_directory(archive_path, tmp_path):
    """Extract entire directory"""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    print(f"\n$ python src/utils/unzip_url.py {archive_path} --select local/ --dir {out_dir}")
    
    result = subprocess.run(['python', 'src/utils/unzip_url.py', str(archive_path),
                           '--select', 'local/',
                           '--dir', str(out_dir)],
                          capture_output=True, text=True)
    
    assert result.returncode == 0
    assert (out_dir / 'local/file.txt').exists()
    assert (out_dir / 'local/another.txt').exists()
    assert (out_dir / 'local/subdir/nested.txt').exists()
    assert (out_dir / 'local/file.txt').read_text() == 'This is a test file'
    assert (out_dir / 'local/another.txt').read_text() == 'Another test file'
    assert (out_dir / 'local/subdir/nested.txt').read_text() == 'Nested test file'

def test_invalid_url():
    """Test invalid URL protocol"""
    print("\n$ python src/utils/unzip_url.py ftp://invalid-protocol.com/file.zip")
    result = subprocess.run(['python', 'src/utils/unzip_url.py', 'ftp://invalid-protocol.com/file.zip'],
                          capture_output=True, text=True)
    assert result.returncode != 0
    assert 'URL must start with http:// or https://' in result.stderr

def test_404_url():
    """Test handling of HTTP errors"""
    print("\n$ python src/utils/unzip_url.py https://httpstat.us/404")
    result = subprocess.run(['python', 'src/utils/unzip_url.py', 'https://httpstat.us/404'],
                          capture_output=True, text=True)
    assert result.returncode != 0
    assert 'HTTP error: 404' in result.stderr

def test_non_archive_url():
    """Test handling of non-zip/gz content"""
    print("\n$ python src/utils/unzip_url.py https://httpstat.us/200")
    result = subprocess.run(['python', 'src/utils/unzip_url.py', 'https://httpstat.us/200'],
                          capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Unexpected content type' in result.stderr 
