"""Main entry point for peTTY."""

from petty.app import PettyApp


def main() -> None:
    """Run the peTTY application."""
    app = PettyApp()
    app.run()


if __name__ == "__main__":
    main()
