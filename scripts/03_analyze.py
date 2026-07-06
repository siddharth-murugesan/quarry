"""Stage 2 CLI: business analysis over labeled clusters."""

import json

from quarry.analysis import run_analysis
from quarry.paths import ANALYSIS


def main() -> None:
    analysis = run_analysis()

    with ANALYSIS.open("w") as f:
        json.dump(analysis, f, indent=2)

    meta = analysis["meta"]
    print(f"\nAnalyzed {meta['total_conversations_analyzed']} conversations across "
          f"{len(analysis['clusters'])} clusters.")
    print(f"Total estimated annual savings: ${meta['total_estimated_annual_savings_usd']:,}")
    print(f"\nSaved to {ANALYSIS.name}")


if __name__ == "__main__":
    main()