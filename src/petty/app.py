"""Main Textual application for peTTY."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static


class PettyApp(App):
    """A Textual app for tracking followers on federated social networks."""

    TITLE = "peTTY"
    SUB_TITLE = "Follower Tracker"
    CSS = """
    Screen {
        align: center middle;
    }

    #welcome {
        width: 60;
        height: 10;
        border: solid $primary;
        content-align: center middle;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Static(
            "Welcome to peTTY!\n\nFollower tracking coming soon...",
            id="welcome"
        )
        yield Footer()


if __name__ == "__main__":
    app = PettyApp()
    app.run()
