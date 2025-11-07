"""Main Textual application for peTTY."""

from datetime import datetime

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Button, Label, LoadingIndicator, ListView, ListItem
from textual.screen import Screen
from textual.worker import Worker, WorkerState

from .config import read_config, ConfigError
from .mastodon_client import (
    create_client,
    verify_credentials,
    fetch_followers,
    fetch_following,
    MastodonClientError,
)
from .database import (
    initialize_database,
    create_snapshot,
    get_all_snapshots,
    delete_snapshot,
    DatabaseError,
)


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
            self.app.push_screen(CreateSnapshotScreen())
        elif event.button.id == "view-snapshots":
            self.app.push_screen(ViewSnapshotsScreen())


class CreateSnapshotScreen(Screen):
    """Screen for creating a new snapshot."""

    CSS = """
    CreateSnapshotScreen {
        align: center middle;
    }

    #snapshot-container {
        width: 70;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    #status-message {
        width: 100%;
        height: auto;
        text-align: center;
        margin: 1 0;
    }

    #loading-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin: 2 0;
    }

    #success-message {
        width: 100%;
        height: auto;
        padding: 1;
        background: $success;
        color: $text;
        text-align: center;
        margin: 1 0;
    }

    #error-message {
        width: 100%;
        height: auto;
        padding: 1;
        background: $error;
        color: $text;
        text-align: center;
        margin: 1 0;
    }

    .action-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        """Initialize the create snapshot screen."""
        super().__init__()
        self.config = None
        self.snapshot_id = None
        self.is_complete = False

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()

        with Container(id="snapshot-container"):
            yield Label("Create New Snapshot", id="title")
            yield Label("", id="status-message")

            with Container(id="loading-container"):
                yield LoadingIndicator()

            with Vertical(classes="action-buttons"):
                yield Button("Back to Menu", id="back-button", variant="default")

        yield Footer()

    def on_mount(self) -> None:
        """Start snapshot creation when screen is mounted."""
        # Load config
        try:
            self.config = read_config()
        except ConfigError as e:
            self._show_error(f"Configuration error: {e}")
            return

        # Start the snapshot creation worker
        self.create_snapshot_worker()

    @work(exclusive=True, thread=True)
    def create_snapshot_worker(self) -> dict:
        """Worker to fetch data and create snapshot.

        Returns:
            Dict with snapshot_id and counts
        """
        try:
            # Update status
            self.app.call_from_thread(
                self._update_status, "Connecting to Mastodon..."
            )

            # Create Mastodon client
            client = create_client(self.config)

            # Fetch followers
            self.app.call_from_thread(
                self._update_status, "Fetching followers..."
            )
            followers = fetch_followers(client)

            # Fetch following
            self.app.call_from_thread(
                self._update_status, "Fetching following..."
            )
            following = fetch_following(client)

            # Create snapshot
            self.app.call_from_thread(
                self._update_status, "Saving snapshot to database..."
            )
            snapshot_id = create_snapshot(followers, following)

            return {
                "snapshot_id": snapshot_id,
                "followers_count": len(followers),
                "following_count": len(following),
            }

        except MastodonClientError as e:
            raise Exception(f"Mastodon API error: {e}")
        except DatabaseError as e:
            raise Exception(f"Database error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        if event.worker.name == "create_snapshot_worker":
            if event.state == WorkerState.SUCCESS:
                result = event.worker.result
                self._show_success(
                    f"Snapshot created successfully!\n\n"
                    f"Snapshot ID: {result['snapshot_id']}\n"
                    f"Followers: {result['followers_count']}\n"
                    f"Following: {result['following_count']}"
                )
            elif event.state == WorkerState.ERROR:
                error_msg = str(event.worker.error)
                self._show_error(error_msg)

    def _update_status(self, message: str) -> None:
        """Update the status message.

        Args:
            message: Status message to display
        """
        status_label = self.query_one("#status-message", Label)
        status_label.update(message)

    def _show_success(self, message: str) -> None:
        """Show success message and hide loading indicator.

        Args:
            message: Success message to display
        """
        self.is_complete = True

        # Hide loading indicator
        loading_container = self.query_one("#loading-container", Container)
        loading_container.display = False

        # Hide status message
        status_label = self.query_one("#status-message", Label)
        status_label.display = False

        # Show success message
        container = self.query_one("#snapshot-container", Container)
        container.mount(Static(message, id="success-message"))

    def _show_error(self, message: str) -> None:
        """Show error message and hide loading indicator.

        Args:
            message: Error message to display
        """
        self.is_complete = True

        # Hide loading indicator
        loading_container = self.query_one("#loading-container", Container)
        loading_container.display = False

        # Hide status message
        status_label = self.query_one("#status-message", Label)
        status_label.display = False

        # Show error message
        container = self.query_one("#snapshot-container", Container)
        container.mount(Static(message, id="error-message"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back-button":
            self.app.pop_screen()


class ViewSnapshotsScreen(Screen):
    """Screen for viewing and managing snapshots."""

    CSS = """
    ViewSnapshotsScreen {
        align: center middle;
    }

    #snapshots-container {
        width: 80;
        height: 90%;
        border: solid $primary;
        padding: 1 2;
    }

    #empty-message {
        width: 100%;
        height: auto;
        text-align: center;
        margin: 2 0;
        color: $text-muted;
    }

    ListView {
        width: 100%;
        height: 1fr;
        margin: 1 0;
        border: solid $panel;
    }

    ListItem {
        padding: 1 2;
    }

    .snapshot-info {
        width: 100%;
    }

    .snapshot-id {
        color: $accent;
    }

    .snapshot-date {
        color: $text;
    }

    .snapshot-count {
        color: $text-muted;
    }

    .action-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    """

    def __init__(self):
        """Initialize the view snapshots screen."""
        super().__init__()
        self.snapshots = []
        self.selected_snapshot_id = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()

        with Container(id="snapshots-container"):
            yield Label("Your Snapshots", id="title")

            # Load snapshots
            try:
                self.snapshots = get_all_snapshots()
            except DatabaseError as e:
                yield Static(f"Error loading snapshots: {e}", id="error-message")
                with Horizontal(classes="action-buttons"):
                    yield Button("Back to Menu", id="back-button", variant="default")
                yield Footer()
                return

            if not self.snapshots:
                yield Static(
                    "No snapshots found.\n\nCreate your first snapshot to get started!",
                    id="empty-message"
                )
            else:
                # Create list view with snapshots
                with ListView(id="snapshots-list"):
                    for snapshot in self.snapshots:
                        # Format the timestamp
                        try:
                            dt = datetime.fromisoformat(snapshot["created_at"])
                            formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            formatted_date = snapshot["created_at"]

                        # Create list item with snapshot info
                        item_text = (
                            f"[bold]Snapshot #{snapshot['id']}[/bold] - "
                            f"{formatted_date} "
                            f"[dim]({snapshot['account_count']} accounts)[/dim]"
                        )

                        yield ListItem(Label(item_text, markup=True), id=f"snapshot-{snapshot['id']}")

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("View Details", id="view-button", variant="primary",
                           disabled=len(self.snapshots) == 0)
                yield Button("Delete", id="delete-button", variant="error",
                           disabled=len(self.snapshots) == 0)
                yield Button("Back to Menu", id="back-button", variant="default")

        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle snapshot selection from list."""
        # Extract snapshot ID from the item ID
        if event.item.id and event.item.id.startswith("snapshot-"):
            snapshot_id_str = event.item.id.replace("snapshot-", "")
            self.selected_snapshot_id = int(snapshot_id_str)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back-button":
            self.app.pop_screen()
        elif event.button.id == "view-button":
            if self.selected_snapshot_id is not None:
                # TODO: Navigate to snapshot detail screen
                self.app.push_screen("snapshot_detail")
            else:
                self.notify("Please select a snapshot first", severity="warning")
        elif event.button.id == "delete-button":
            if self.selected_snapshot_id is not None:
                self._delete_selected_snapshot()
            else:
                self.notify("Please select a snapshot first", severity="warning")

    def _delete_selected_snapshot(self) -> None:
        """Delete the currently selected snapshot."""
        if self.selected_snapshot_id is None:
            return

        try:
            delete_snapshot(self.selected_snapshot_id)
            self.notify(f"Snapshot #{self.selected_snapshot_id} deleted successfully",
                       severity="information")

            # Refresh the screen
            self.app.pop_screen()
            self.app.push_screen(ViewSnapshotsScreen())

        except DatabaseError as e:
            self.notify(f"Error deleting snapshot: {e}", severity="error")


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
