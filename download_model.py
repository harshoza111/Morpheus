"""
download_model.py — Standalone Llama 3.2 3B model downloader.

Reads the HF_TOKEN from `.env` and uses huggingface_hub to download
the Llama-3.2-3B model files locally.
"""

import os
import sys
from pathlib import Path

def parse_env():
    """Parse .env file manually to avoid external dependencies before pip install."""
    env_path = Path(".env")
    if not env_path.exists():
        return {}
    env_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                env_vars[key] = val
    return env_vars

def main():
    env = parse_env()
    hf_token = env.get("HF_TOKEN") or os.environ.get("HF_TOKEN")
    
    if not hf_token:
        print("=" * 80)
        print("ERROR: HF_TOKEN not found in .env or environment variables.")
        print("Please perform the following steps:")
        print("  1. Accept Llama 3.2 license at: https://huggingface.co/meta-llama/Llama-3.2-3B")
        print("  2. Create a READ access token at: https://huggingface.co/settings/tokens")
        print("  3. Add the token to your .env file:")
        print("     HF_TOKEN=your_access_token_here")
        print("=" * 80)
        sys.exit(1)
        
    print("HF_TOKEN detected. Checking huggingface_hub library...")
    
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("huggingface_hub not installed. Installing it via pip...")
        import subprocess
        # Use python from active environment
        python_exe = sys.executable
        subprocess.run([python_exe, "-m", "pip", "install", "huggingface_hub"], check=True)
        from huggingface_hub import snapshot_download

    local_dir = Path("local_models/Llama-3.2-3B")
    local_dir.mkdir(parents=True, exist_ok=True)
    
    print("-" * 80)
    print(f"Downloading model 'meta-llama/Llama-3.2-3B'...")
    print(f"Destination: {local_dir.resolve()}")
    print("This may take some time depending on your network connection (~6GB)...")
    print("-" * 80)
    
    try:
        snapshot_download(
            repo_id="meta-llama/Llama-3.2-3B",
            local_dir=str(local_dir),
            token=hf_token,
            local_dir_use_symlinks=False
        )
        print("\nSUCCESS: Model files downloaded successfully!")
    except Exception as e:
        print(f"\nERROR: Model download failed: {e}")
        print("Make sure your token has access permissions and you accepted terms on Hugging Face.")
        sys.exit(1)

if __name__ == "__main__":
    main()
