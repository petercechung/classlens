"""End-to-end pipeline: generate -> ingest -> process -> deliver."""
import subprocess
import sys
import os

HERE = os.path.dirname(__file__)


def main():
    # 1. generate synthetic answer-sheet data (skip if raw already present)
    raw = os.path.join(HERE, "data", "raw", "responses.csv")
    if not os.path.exists(raw) or "--regen" in sys.argv:
        subprocess.check_call([sys.executable,
                               os.path.join(HERE, "data", "generate_synthetic.py")])
    # 2-4. ingest -> process -> deliver
    sys.path.insert(0, os.path.join(HERE, "src"))
    import ingest, process, deliver
    ingest.ingest()
    process.build()
    deliver.write()
    print("\nDone. Open classlens/public/index.html "
          "(or deploy the public/ folder).")


if __name__ == "__main__":
    main()
