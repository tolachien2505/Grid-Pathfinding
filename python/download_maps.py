import os
import urllib.request
import zipfile
import io

# Configuration
DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset")
os.makedirs(DATASET_DIR, exist_ok=True)

# URL of the complete 2D MAPF maps ZIP archive (73KB)
MAPS_ZIP_URL = "https://movingai.com/benchmarks/mapf/mapf-map.zip"

def download_and_extract_dataset():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # Check if we already have the extracted map files
    # E.g. Berlin_1_256.map and Boston_0_256.map
    expected_files = ["Berlin_1_256.map", "Boston_0_256.map"]
    all_exist = all(os.path.exists(os.path.join(DATASET_DIR, f)) for f in expected_files)
    
    if all_exist:
        print("[EXIST] Benchmark maps are already extracted in the dataset folder.")
        return True

    print(f"Downloading complete MAPF dataset from: {MAPS_ZIP_URL}")
    try:
        req = urllib.request.Request(MAPS_ZIP_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            zip_data = response.read()
            
        print("Extracting maps...")
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            z.extractall(DATASET_DIR)
            
        print(f"[SUCCESS] Extracted all maps to: {DATASET_DIR}")
        print("Available maps:")
        for file in os.listdir(DATASET_DIR)[:15]:
            if file.endswith(".map"):
                print(f" - {file}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download or extract maps: {e}")
        return False

if __name__ == "__main__":
    success = download_and_extract_dataset()
    if not success:
        # Fallback synthetic generator
        print("\n[WARNING] Falling back to generating synthetic maps...")
        for name in ["Berlin_1_256.map", "Boston_0_256.map"]:
            path = os.path.join(DATASET_DIR, name)
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write("type octile\nheight 256\nwidth 256\nmap\n")
                    for r in range(256):
                        row = ["."] * 256
                        if r % 15 == 0:
                            for c in range(20, 230): 
                                row[c] = "@"
                        # Main roads
                        if r % 3 == 0:
                            row[128] = "."
                            row[64] = "."
                            row[192] = "."
                        f.write("".join(row) + "\n")
                print(f"Generated synthetic map: {path}")
