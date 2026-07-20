#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tarfile
import shutil

def format_ar_header(name, size, timestamp=0, owner=0, group=0, mode=0o100644):
    name_bytes = name.encode('ascii')
    if len(name_bytes) > 16:
        raise ValueError(f"Filename too long for ar archive: {name}")
    name_field = name_bytes.ljust(16)
    
    timestamp_field = str(int(timestamp)).encode('ascii').ljust(12)
    owner_field = str(int(owner)).encode('ascii').ljust(6)
    group_field = str(int(group)).encode('ascii').ljust(6)
    mode_field = f"{mode:o}".encode('ascii').ljust(8)
    size_field = str(int(size)).encode('ascii').ljust(10)
    magic = b"\x60\x0a"
    
    header = name_field + timestamp_field + owner_field + group_field + mode_field + size_field + magic
    assert len(header) == 60, f"AR header length is {len(header)} instead of 60"
    return header

def create_ar_archive(output_path, files):
    print(f"Creating ar archive at: {output_path}")
    with open(output_path, 'wb') as ar_file:
        ar_file.write(b"!<arch>\n")
        
        for file_path in files:
            name = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)
            
            # Write header
            header = format_ar_header(name, size, timestamp=mtime)
            ar_file.write(header)
            
            # Write file content
            with open(file_path, 'rb') as f:
                ar_file.write(f.read())
                
            # Pad to even bytes
            if size % 2 != 0:
                ar_file.write(b"\n")

def tar_filter(tarinfo):
    basename = os.path.basename(tarinfo.name)
    # Exclude installer, readme, git files, python compiled files, and build/github files
    if basename in ["installer.sh", "README.md", ".git", ".gitignore", "__pycache__", "build_ipk.py", ".github"] or basename.endswith(".pyc") or basename.endswith(".pyo"):
        return None
    
    # Normalize ownership and permissions
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = "root"
    tarinfo.gname = "root"
    tarinfo.name = tarinfo.name.replace("\\", "/")
    
    if tarinfo.isdir():
        tarinfo.mode = 0o755
    else:
        tarinfo.mode = 0o644
        
    return tarinfo

def get_version(base_dir):
    import re
    plugin_path = os.path.join(base_dir, "plugin.py")
    if not os.path.exists(plugin_path):
        return "1.0"
    try:
        with open(plugin_path, "r", encoding="utf-8") as f:
            content = f.read()
            m = re.search(r'PLUGIN_VERSION\s*=\s*["\']([^"\']+)["\']', content)
            if m:
                ver = m.group(1)
                if ver.lower().startswith('v'):
                    ver = ver[1:]
                return ver
    except Exception as e:
        print(f"Warning: Failed to parse version from plugin.py: {e}")
    return "1.0"

def main():
    import sys
    pkg_name = "enigma2-plugin-extensions-lastscannedanalyzer"
    arch = "all"
    
    # Use workspace dir as reference point
    base_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(base_dir, "build_tmp")
    
    # Determine version: command-line argument has priority, then auto-detection from plugin.py
    if len(sys.argv) > 1:
        version = sys.argv[1]
        print(f"Using version from command line: {version}")
    else:
        version = get_version(base_dir)
        print(f"Auto-detected version from plugin.py: {version}")
        
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    try:
        # 1. Create control file content
        control_content = f"""Package: {pkg_name}
Version: {version}
Description: LastScanned Analyzer for Enigma2 (Premium Edition)
Section: extra
Priority: optional
Maintainer: andrejicd
Architecture: {arch}
Source: https://github.com/andrejicd/Last-Scanned-Analyzer
"""
        control_path = os.path.join(build_dir, "control")
        with open(control_path, "w", newline="\n") as f:
            f.write(control_content)
            
        # 2. Create control.tar.gz
        control_tar_path = os.path.join(build_dir, "control.tar.gz")
        print("Packaging control.tar.gz...")
        with tarfile.open(control_tar_path, "w:gz") as tar:
            tar.add(control_path, arcname="control", filter=tar_filter)
            
        # 3. Create data.tar.gz
        data_tar_path = os.path.join(build_dir, "data.tar.gz")
        print("Packaging data.tar.gz...")
        
        plugin_src_dir = base_dir
        with tarfile.open(data_tar_path, "w:gz") as tar:
            # Add LastScannedAnalyzer directory mapped to enigma2 path
            tar.add(
                plugin_src_dir,
                arcname="usr/lib/enigma2/python/Plugins/Extensions/LastScannedAnalyzer",
                filter=tar_filter
            )
            
        # 4. Create debian-binary
        debian_binary_path = os.path.join(build_dir, "debian-binary")
        with open(debian_binary_path, "w", newline="\n") as f:
            f.write("2.0\n")
            
        # 5. Package everything into the final .ipk file
        ipk_filename = f"{pkg_name}_{version}_{arch}.ipk"
        ipk_path = os.path.join(base_dir, ipk_filename)
        
        create_ar_archive(
            ipk_path,
            [debian_binary_path, control_tar_path, data_tar_path]
        )
        
        print("==================================================")
        print(f"Successfully built: {ipk_filename}")
        print("==================================================")
        
    finally:
        # Clean up build temp files
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

if __name__ == "__main__":
    main()
