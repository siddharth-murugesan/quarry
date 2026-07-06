"""Stage 0 CLI: generate the synthetic conversation dataset."""

from quarry.generation import generate_dataset
from quarry.paths import CONVERSATIONS


def main() -> None:
    count = generate_dataset()
    print(f"\nWrote {count} conversations to {CONVERSATIONS}")


if __name__ == "__main__":
    main()