"""Main Textual application for peTTY."""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Button
from textual.screen import Screen

from .config import read_config, ConfigError
from .mastodon_client import create_client, verify_credentials, MastodonClientError
from .database import initialize_database


class MainMenuScreen(Screen):
    """Main menu screen for peTTY."""

    CSS = """
    MainMenuScreen {
        align: center middle;
    }

    #menu-container {
        width: 70;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }

    #user-info {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 1;
        background: $boost;
        color: $text;
        text-align: center;
    }

    #error-message {
        width: 100%;
        height: auto;
        margin-bottom: 1;
        padding: 1;
        background: $error;
        color: $text;
        text-align: center;
    }

    .menu-buttons {
        width: 100%;
        height: auto;
        align: center middle;
    }

    Button {
        width: 100%;
        margin: 1 0;
    }
    """

    def __init__(self):
        """Initialize the main menu screen."""
        super().__init__()
        self.config = None
        self.user_info = None
        self.error_message = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()

        with Container(id="menu-container"):
            yield Static("peTTY - Mastodon Follower Tracker", classes="title")

            # Try to load config and user info
            try:
                self.config = read_config()
                client = create_client(self.config)
                self.user_info = verify_credentials(client)

                # Show user info
                user_text = (
                    f"Logged in as: @{self.user_info['username']}\n"
                    f"{self.user_info['display_name']}\n"
                    f"Followers: {self.user_info['followers_count']} | "
                    f"Following: {self.user_info['following_count']}"
                )
                yield Static(user_text, id="user-info")

            except ConfigError as e:
                self.error_message = str(e)
                error_text = (
                    f"Configuration Error\n\n{self.error_message}\n\n"
                    "Please set up your config file at:\n"
                    "~/.config/petty/config.toml\n\n"
                    "See README.md for instructions."
                )
                yield Static(error_text, id="error-message")

            except MastodonClientError as e:
                self.error_message = str(e)
                error_text = (
                    f"Mastodon API Error\n\n{self.error_message}\n\n"
                    "Please check your credentials and network connection."
                )
                yield Static(error_text, id="error-message")

            # Menu buttons
            with Vertical(classes="menu-buttons"):
                yield Button("Create Snapshot", id="create-snapshot",
                           variant="primary", disabled=self.error_message is not None)
                yield Button("View Snapshots", id="view-snapshots",
                           variant="default", disabled=self.error_message is not None)
                yield Button("Quit", id="quit-button", variant="error")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "quit-button":
            self.app.exit()
        elif event.button.id == "create-snapshot":
            # TODO: Navigate to create snapshot screen
            self.app.push_screen("create_snapshot")
        elif event.button.id == "view-snapshots":
            # TODO: Navigate to view snapshots screen
            self.app.push_screen("view_snapshots")


class PettyApp(App):
    """A Textual app for tracking followers on federated social networks."""

    TITLE = "peTTY"
    SUB_TITLE = "Follower Tracker"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initialize app on mount."""
        # Initialize database
        initialize_database()

        # Push main menu screen
        self.push_screen(MainMenuScreen())


if __name__ == "__main__":
    app = PettyApp()
    app.run()
