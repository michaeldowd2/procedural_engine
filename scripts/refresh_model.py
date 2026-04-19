import os
import sys
import argparse
import subprocess
import glob

def run_script(script_name, args=None):
    """Run a python script and wait for it to finish."""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    print(f"\n>>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error: {script_name} failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def main():
    parser = argparse.ArgumentParser(description="Refresh model data and samples.")
    parser.add_argument("--model", default="song", help="Model name (default: song)")
    parser.add_argument("--max-rules", type=int, default=5000)
    parser.add_argument("--max-per-source", type=int, default=2000)
    args = parser.parse_args()

    # Ensure we are in the root directory
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    # 1. Mine Rules and build Graph Data
    run_script("scripts/generate_model_data.py", [
        "--model", args.model,
        "--max-rules", str(args.max_rules),
        "--max-per-source", str(args.max_per_source)
    ])

    # 2. Generate Embeddings (if instrument data exists)
    if args.model == "song":
        run_script("scripts/generate_embeddings.py")

    # 3. Generate Samples
    run_script("scripts/generate_samples.py", ["--model", args.model])

    print("\n" + "="*40)
    print(f"Successfully refreshed model: {args.model}")
    print("="*40)

if __name__ == "__main__":
    main()
