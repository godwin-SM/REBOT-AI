#!/usr/bin/env python
"""
Size optimization verification script.
Checks component sizes and reports on deployment footprint.
"""

import os
import sys
from pathlib import Path

def get_dir_size(path):
    """Calculate directory size in MB"""
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir(follow_symlinks=False):
            try:
                total += get_dir_size(entry.path)
            except PermissionError:
                pass
    return total / (1024 * 1024)  # Convert to MB

def main():
    print("🔍 REBOT AI - Size Analysis Report\n")
    print("=" * 50)
    
    base_path = Path(__file__).parent
    
    # Check key directories
    dirs_to_check = {
        "Source Code": base_path,
        "Static Files": base_path / "static",
        "Uploads": base_path / "uploads",
        "Vector DB": base_path / "vector_db",
    }
    
    total_size = 0
    for name, path in dirs_to_check.items():
        if path.exists():
            size = get_dir_size(path)
            total_size += size
            status = "✅" if size < 100 else "⚠️" if size < 300 else "❌"
            print(f"{status} {name:20} {size:10.2f} MB")
    
    print("=" * 50)
    print(f"Total project size:   {total_size:.2f} MB")
    print(f"Target limit:         500.00 MB")
    print(f"Status:               {'✅ PASS' if total_size < 500 else '❌ FAIL'}")
    print("\n📦 Deployment Components:")
    print("  • FastAPI + Uvicorn:    ~50 MB")
    print("  • Python dependencies:  ~150 MB (numpy, requests, chromadb, etc.)")
    print("  • Embedding model:      ~80 MB (multi-qa-MiniLM-L6-cos-v1)")
    print("  • ONNX Runtime:         ~100 MB")
    print("  • ChromaDB:            ~30 MB")
    print("  • pypdf + docx:        ~20 MB")
    print("  • Source code + static: ~20 MB")
    print("                         --------")
    print("  Total estimated:       ~450 MB ✅")
    print("\n💡 Optimization Tips:")
    print("  1. Use .dockerignore to exclude cache files")
    print("  2. Use --no-cache-dir with pip install")
    print("  3. Use python:3.12-slim base image")
    print("  4. Remove unused dependencies")
    print("  5. Compress static files if possible")

if __name__ == "__main__":
    main()
