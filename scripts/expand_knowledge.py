import subprocess
import sys
import os

def run_script(script_path):
    print(f"\n--- Running {script_path} ---")
    result = subprocess.run([sys.executable, script_path], capture_output=False, text=True)
    if result.returncode != 0:
        print(f"❌ Error running {script_path}")
        return False
    return True

def main():
    # Ensure we are in the root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    print(f"📂 Working directory: {os.getcwd()}")

    # 1. Download datasets
    if not run_script("scripts/dowload_dataset.py"):
        return

    # 2. Map symptoms
    if not run_script("scripts/auto_mapping.py"):
        return

    # 3. Ingest into DB
    if not run_script("scripts/ingest_knowledge_chunks.py"):
        return

    print("\n🚀 ALL STEPS COMPLETED SUCCESSFULLY!")
    print("Your chatbot now has a more diverse and comprehensive knowledge base.")

if __name__ == "__main__":
    main()
