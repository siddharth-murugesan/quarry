"""Central path definitions. Import from here, don't hardcode strings."""

from pathlib import Path

# quarry/paths.py lives at <project_root>/quarry/paths.py
# So parents[1] is the project root.
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"

# Stage 0 artifact
CONVERSATIONS = RAW_DIR / "conversations.jsonl"

# Stage 1 artifacts
EMBEDDINGS = PROCESSED_DIR / "embeddings.npy"
REDUCED_EMBEDDINGS = PROCESSED_DIR / "reduced_embeddings.npy"
CLUSTERS = PROCESSED_DIR / "clusters.jsonl"

# Stage 3 artifacts
REPORT = OUTPUT_DIR / "report.html"
SANITY_PLOT = OUTPUT_DIR / "sanity_plot.png"


def ensure_dirs() -> None:
    """Create all data directories if missing. Safe to call multiple times."""
    for d in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)