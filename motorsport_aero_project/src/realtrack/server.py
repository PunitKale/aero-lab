"""python -m src.realtrack.server [--port 8766] [--download]"""
import argparse
import uvicorn
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.realtrack import circuit

def main():
    parser = argparse.ArgumentParser(description="Aero Lab API Server")
    parser.add_argument("--port", type=int, default=8766, help="Port to run the API server on")
    parser.add_argument("--download", action="store_true", help="Pre-download all circuit OSM data")
    args = parser.parse_args()

    if args.download:
        print("Pre-downloading circuit OSM data...")
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "circuits.json"
        cache_dir = Path(__file__).resolve().parent.parent.parent / ".cache"
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
            for cid, cinfo in data.items():
                print(f"Downloading {cid}...")
                try:
                    circuit.load_circuit(cid, cinfo['circuit_id'], cache_dir)
                except Exception as e:
                    print(f"Failed to download {cid}: {e}")
        print("Download complete.")

    print(f"Starting server on port {args.port}...")
    uvicorn.run("src.realtrack.api:app", host="0.0.0.0", port=args.port, reload=True)

if __name__ == "__main__":
    main()
