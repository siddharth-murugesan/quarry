"""Stage 3 CLI: render the HTML report."""

from quarry.reporting import render_report


def main() -> None:
    render_report()
    print("Report rendering complete.")


if __name__ == "__main__":
    main()