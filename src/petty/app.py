"""Main Textual application for peTTY."""

from datetime import datetime

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Label,
    LoadingIndicator,
    ListView,
    ListItem,
    TabbedContent,
    TabPane,
    Input,
)
from textual.screen import Screen
from textual.worker import Worker, WorkerState

from .config import read_config, config_exists, ConfigError
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
    get_snapshot_accounts,
    get_snapshot_diff,
    delete_snapshot,
    DatabaseError,
)
from .oauth import (
    register_app,
    get_authorization_url,
    exchange_code_for_token,
    complete_oauth_setup,
    open_browser,
    OAuthError,
)


class OAuthSetupScreen(Screen):
    """Screen for OAuth setup flow."""

    BINDINGS = [
        ("escape", "quit", "Quit"),
    ]

    CSS = """
    OAuthSetupScreen {
        align: center middle;
    }

    #setup-container {
        width: 90%;
        height: auto;
        border: thick $primary;
        padding: 1 2;
    }

    .setup-instructions {
        width: 100%;
        margin: 1 0;
        padding: 1;
        background: $panel;
    }

    Input {
        width: 100%;
        margin: 1 0;
    }

    .auth-url-box {
        width: 100%;
        margin: 1 0;
        padding: 1;
        background: $boost;
        border: solid $accent;
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

    #error-message {
        width: 100%;
        padding: 1;
        background: $error;
        color: $text;
        text-align: center;
        margin: 1 0;
    }

    #success-message {
        width: 100%;
        padding: 1;
        background: $success;
        color: $text;
        text-align: center;
        margin: 1 0;
    }

    #loading-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin: 2 0;
    }
    """

    def __init__(self):
        """Initialize OAuth setup screen."""
        super().__init__()
        self.step = "server_url"  # server_url, show_auth_url, enter_code, processing, complete
        self.server_url = ""
        self.client_id = ""
        self.client_secret = ""
        self.auth_url = ""

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()

        with Container(id="setup-container"):
            yield Static("OAuth Setup", classes="screen-title")
            yield Static(
                "Welcome to peTTY! Let's connect your Mastodon account.\n\n"
                "Enter your Mastodon server URL (e.g., https://mastodon.social):",
                classes="setup-instructions",
                id="instructions"
            )

            yield Input(
                placeholder="https://mastodon.social",
                id="server-url-input",
            )

            with Horizontal(classes="action-buttons", id="button-container"):
                yield Button("Continue", id="continue-button", variant="primary")
                yield Button("Quit", id="quit-button", variant="error")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "quit-button":
            self.app.exit()
        elif event.button.id == "continue-button":
            if self.step == "server_url":
                self._handle_server_url_submit()
            elif self.step == "enter_code":
                self._handle_auth_code_submit()
        elif event.button.id == "open-browser-button":
            open_browser(self.auth_url)
            self.notify("Browser opened. Please authorize the app.", severity="information")
        elif event.button.id == "done-button":
            # Setup complete, navigate to main menu
            self.app.pop_screen()
            self.app.push_screen(MainMenuScreen())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "server-url-input" and self.step == "server_url":
            self._handle_server_url_submit()
        elif event.input.id == "auth-code-input" and self.step == "enter_code":
            self._handle_auth_code_submit()

    def _handle_server_url_submit(self) -> None:
        """Handle server URL submission."""
        server_input = self.query_one("#server-url-input", Input)
        server_url = server_input.value.strip()

        if not server_url:
            self.notify("Please enter a server URL", severity="error")
            return

        # Add https:// if not present
        if not server_url.startswith(("http://", "https://")):
            server_url = f"https://{server_url}"

        self.server_url = server_url

        # Start registration worker
        self._show_loading("Registering app with server...")
        self.register_app_worker()

    def _handle_auth_code_submit(self) -> None:
        """Handle authorization code submission."""
        code_input = self.query_one("#auth-code-input", Input)
        auth_code = code_input.value.strip()

        if not auth_code:
            self.notify("Please enter the authorization code", severity="error")
            return

        # Start token exchange worker
        self._show_loading("Exchanging code for access token...")
        self.exchange_token_worker(auth_code)

    @work(exclusive=True, thread=True)
    def register_app_worker(self) -> dict:
        """Worker to register app with Mastodon server."""
        try:
            client_id, client_secret = register_app(self.server_url)
            auth_url = get_authorization_url(self.server_url, client_id, client_secret)

            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_url": auth_url,
            }
        except OAuthError as e:
            raise Exception(f"OAuth error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

    @work(exclusive=True, thread=True)
    def exchange_token_worker(self, auth_code: str) -> str:
        """Worker to exchange authorization code for access token."""
        try:
            access_token = exchange_code_for_token(
                self.server_url,
                self.client_id,
                self.client_secret,
                auth_code,
            )
            return access_token
        except OAuthError as e:
            raise Exception(f"OAuth error: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        if event.worker.name == "register_app_worker":
            if event.state == WorkerState.SUCCESS:
                result = event.worker.result
                self.client_id = result["client_id"]
                self.client_secret = result["client_secret"]
                self.auth_url = result["auth_url"]
                self._show_auth_url_step()
            elif event.state == WorkerState.ERROR:
                self._show_error(str(event.worker.error))

        elif event.worker.name == "exchange_token_worker":
            if event.state == WorkerState.SUCCESS:
                access_token = event.worker.result
                self._save_credentials(access_token)
            elif event.state == WorkerState.ERROR:
                self._show_error(str(event.worker.error))

    def _show_loading(self, message: str) -> None:
        """Show loading indicator with message."""
        self.step = "processing"

        # Clear container and show loading
        container = self.query_one("#setup-container", Container)
        container.remove_children()

        container.mount(Static("OAuth Setup", classes="screen-title"))
        container.mount(Static(message, classes="setup-instructions"))

        # Mount the container first, then add the loading indicator
        loading_container = Container(id="loading-container")
        container.mount(loading_container)
        loading_container.mount(LoadingIndicator())

    def _show_auth_url_step(self) -> None:
        """Show the authorization URL step."""
        self.step = "enter_code"

        # Clear container and show auth URL
        container = self.query_one("#setup-container", Container)
        container.remove_children()

        container.mount(Static("OAuth Setup - Step 2", classes="screen-title"))

        instructions = Static(
            "Great! Now you need to authorize peTTY to access your Mastodon account.\n\n"
            "Click the button below to open your browser, or manually visit this URL:",
            classes="setup-instructions"
        )
        container.mount(instructions)

        # Show the auth URL in a copyable box
        auth_url_box = Static(self.auth_url, classes="auth-url-box")
        container.mount(auth_url_box)

        # Add open browser button
        browser_container = Horizontal(classes="action-buttons")
        container.mount(browser_container)
        browser_container.mount(Button("Open Browser", id="open-browser-button", variant="success"))

        # Instructions for code entry
        code_instructions = Static(
            "\nAfter authorizing, you'll receive an authorization code.\n"
            "Enter it below:",
            classes="setup-instructions"
        )
        container.mount(code_instructions)

        # Input for auth code
        code_input = Input(
            placeholder="Authorization code",
            id="auth-code-input",
        )
        container.mount(code_input)

        # Buttons
        button_container = Horizontal(classes="action-buttons")
        container.mount(button_container)
        button_container.mount(Button("Continue", id="continue-button", variant="primary"))
        button_container.mount(Button("Quit", id="quit-button", variant="error"))

        # Focus the input
        code_input.focus()

    def _save_credentials(self, access_token: str) -> None:
        """Save OAuth credentials to config."""
        try:
            complete_oauth_setup(
                self.server_url,
                self.client_id,
                self.client_secret,
                access_token,
            )
            self._show_success()
        except Exception as e:
            self._show_error(f"Failed to save credentials: {e}")

    def _show_success(self) -> None:
        """Show success message."""
        self.step = "complete"

        container = self.query_one("#setup-container", Container)
        container.remove_children()

        container.mount(Static("Setup Complete!", classes="screen-title"))

        success_msg = Static(
            "Your Mastodon account has been connected successfully!\n\n"
            "You can now use peTTY to track your followers.",
            id="success-message"
        )
        container.mount(success_msg)

        button_container = Horizontal(classes="action-buttons")
        container.mount(button_container)
        button_container.mount(Button("Get Started", id="done-button", variant="primary"))

    def _show_error(self, error_message: str) -> None:
        """Show error message and allow retry."""
        container = self.query_one("#setup-container", Container)

        # Check if error message already exists
        try:
            existing_error = container.query_one("#error-message")
            existing_error.update(error_message)
        except Exception:
            # Add new error message
            error_widget = Static(error_message, id="error-message")
            container.mount(error_widget)

        self.notify("An error occurred. Please try again.", severity="error")

    def action_quit(self) -> None:
        """Action to quit."""
        self.app.exit()


class MainMenuScreen(Screen):
    """Main menu screen for peTTY."""

    BINDINGS = [
        ("c", "create_snapshot", "Create Snapshot"),
        ("v", "view_snapshots", "View Snapshots"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    MainMenuScreen {
        align: center middle;
    }

    #menu-container {
        width: 90%;
        height: auto;
        border: thick $primary;
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
        margin-top: 1;
    }

    Button {
        margin: 0 1;
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
            yield Static("peTTY - Mastodon Follower Tracker", classes="screen-title")

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
            with Horizontal(classes="menu-buttons"):
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

    def action_create_snapshot(self) -> None:
        """Action to create a snapshot (keyboard shortcut)."""
        if self.error_message is None:
            self.app.push_screen(CreateSnapshotScreen())
        else:
            self.notify("Please fix configuration errors first", severity="warning")

    def action_view_snapshots(self) -> None:
        """Action to view snapshots (keyboard shortcut)."""
        if self.error_message is None:
            self.app.push_screen(ViewSnapshotsScreen())
        else:
            self.notify("Please fix configuration errors first", severity="warning")

    def action_quit(self) -> None:
        """Action to quit (keyboard shortcut)."""
        self.app.exit()


class CreateSnapshotScreen(Screen):
    """Screen for creating a new snapshot."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    CreateSnapshotScreen {
        align: center middle;
    }

    #snapshot-container {
        width: 90%;
        height: auto;
        border: thick $primary;
        padding: 1 2;
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
            yield Static("Create New Snapshot", classes="screen-title")
            yield Label("", id="status-message")

            with Container(id="loading-container"):
                yield LoadingIndicator()

            with Vertical(classes="action-buttons"):
                yield Button("Back", id="back-button", variant="default")

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

    def action_back(self) -> None:
        """Action to go back (keyboard shortcut)."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Action to quit (keyboard shortcut)."""
        self.app.exit()


class ViewSnapshotsScreen(Screen):
    """Screen for viewing and managing snapshots."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("enter", "view_selected", "View"),
        ("d", "delete_selected", "Delete"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    ViewSnapshotsScreen {
        align: center middle;
    }

    #snapshots-container {
        width: 90%;
        height: 90%;
        border: thick $primary;
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
            yield Static("Your Snapshots", classes="screen-title")

            # Load snapshots
            try:
                self.snapshots = get_all_snapshots()
            except DatabaseError as e:
                yield Static(f"Error loading snapshots: {e}", id="error-message")
                with Horizontal(classes="action-buttons"):
                    yield Button("Back", id="back-button", variant="default")
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
                yield Button("Back", id="back-button", variant="default")

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
                self.app.push_screen(SnapshotDetailScreen(self.selected_snapshot_id))
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

    def action_back(self) -> None:
        """Action to go back (keyboard shortcut)."""
        self.app.pop_screen()

    def action_view_selected(self) -> None:
        """Action to view selected snapshot details (keyboard shortcut)."""
        if self.selected_snapshot_id is not None:
            self.app.push_screen(SnapshotDetailScreen(self.selected_snapshot_id))
        else:
            self.notify("Please select a snapshot first", severity="warning")

    def action_delete_selected(self) -> None:
        """Action to delete selected snapshot (keyboard shortcut)."""
        if self.selected_snapshot_id is not None:
            self._delete_selected_snapshot()
        else:
            self.notify("Please select a snapshot first", severity="warning")

    def action_quit(self) -> None:
        """Action to quit (keyboard shortcut)."""
        self.app.exit()


class SnapshotDetailScreen(Screen):
    """Screen for viewing detailed snapshot analysis."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("1", "tab_1", "Not Following"),
        ("2", "tab_2", "Not Followed"),
        ("3", "tab_3", "New"),
        ("4", "tab_4", "Lost"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    SnapshotDetailScreen {
        align: center top;
    }

    #detail-container {
        width: 90%;
        height: 95%;
        border: thick $primary;
        padding: 1 2;
        margin: 1 0;
    }

    #snapshot-header {
        width: 100%;
        height: auto;
        text-align: center;
        color: $accent;
        margin-bottom: 1;
        padding: 1;
        background: $boost;
    }

    TabbedContent {
        width: 100%;
        height: 1fr;
        margin: 1 0;
    }

    TabPane {
        padding: 1;
    }

    .account-list {
        width: 100%;
        height: 1fr;
    }

    .list-header {
        width: 100%;
        padding: 0 0 1 0;
        color: $text;
    }

    .list-separator {
        width: 100%;
        height: 1;
        background: $panel;
        margin-bottom: 1;
    }

    .account-row {
        width: 100%;
        padding: 0;
    }

    .account-row Static {
        color: $text;
    }

    .empty-list {
        width: 100%;
        height: auto;
        text-align: center;
        padding: 2;
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

    def __init__(self, snapshot_id: int):
        """Initialize the snapshot detail screen.

        Args:
            snapshot_id: ID of the snapshot to display
        """
        super().__init__()
        self.snapshot_id = snapshot_id

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()

        with Container(id="detail-container"):
            # Header with snapshot info
            try:
                snapshots = get_all_snapshots()
                current_snapshot = next(
                    (s for s in snapshots if s["id"] == self.snapshot_id), None
                )

                if current_snapshot:
                    dt = datetime.fromisoformat(current_snapshot["created_at"])
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                    header_text = (
                        f"Snapshot #{self.snapshot_id}\n"
                        f"{formatted_date}"
                    )
                    yield Static(header_text, id="snapshot-header")
            except Exception:
                yield Static(f"Snapshot #{self.snapshot_id}", id="snapshot-header")

            # Tabbed content for the 4 lists
            with TabbedContent():
                # Tab 1: Who doesn't follow you back
                with TabPane("Not Following Back"):
                    yield from self._create_account_list("not_following_back")

                # Tab 2: Who you're not following back
                with TabPane("Not Followed Back"):
                    yield from self._create_account_list("not_followed_back")

                # Tab 3: New followers (since previous snapshot)
                with TabPane("New Followers"):
                    yield from self._create_diff_list("new_followers")

                # Tab 4: Unfollowers (since previous snapshot)
                with TabPane("Unfollowers"):
                    yield from self._create_diff_list("unfollowers")

            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("Back", id="back-button", variant="default")

        yield Footer()

    def _create_list_header(self, title: str, count: int) -> ComposeResult:
        """Create a header for an account list.

        Args:
            title: The list title (e.g., "Not Following Back")
            count: Number of accounts in the list

        Returns:
            Generator yielding header widgets
        """
        yield Static(f"{title} ({count} accounts)", classes="list-header")
        yield Static("", classes="list-separator")

    def _get_list_title(self, list_type: str) -> str:
        """Get display title for each list type.

        Args:
            list_type: Type of list (relationship filter or diff type)

        Returns:
            Human-readable title for the list
        """
        titles = {
            "not_following_back": "Not Following Back",
            "not_followed_back": "Not Followed Back",
            "new_followers": "New Followers",
            "unfollowers": "Unfollowers",
        }
        return titles.get(list_type, "Accounts")

    def _create_account_list(self, relationship_filter: str) -> ComposeResult:
        """Create a scrollable list of accounts.

        Args:
            relationship_filter: Filter type for get_snapshot_accounts

        Returns:
            Generator yielding VerticalScroll with account items
        """
        try:
            accounts = get_snapshot_accounts(self.snapshot_id, relationship_filter)
            title = self._get_list_title(relationship_filter)

            with VerticalScroll(classes="account-list"):
                if not accounts:
                    yield from self._create_list_header(title, 0)
                    empty_msg = self._get_empty_message(relationship_filter)
                    yield Static(empty_msg, classes="empty-list")
                else:
                    yield from self._create_list_header(title, len(accounts))
                    for account in accounts:
                        yield self._create_account_widget(account)

        except DatabaseError as e:
            with VerticalScroll(classes="account-list"):
                yield Static(f"Error loading accounts: {e}", classes="empty-list")

    def _create_diff_list(self, diff_type: str) -> ComposeResult:
        """Create a scrollable list showing diff between snapshots.

        Args:
            diff_type: Either 'new_followers' or 'unfollowers'

        Returns:
            Generator yielding VerticalScroll with account items
        """
        try:
            # Get all snapshots to find the previous one
            snapshots = get_all_snapshots()
            snapshot_ids = [s["id"] for s in snapshots]

            # Find the previous snapshot
            try:
                current_index = snapshot_ids.index(self.snapshot_id)
                if current_index < len(snapshot_ids) - 1:
                    previous_snapshot_id = snapshot_ids[current_index + 1]

                    # Get the diff
                    new_followers, unfollowers = get_snapshot_diff(
                        self.snapshot_id, previous_snapshot_id
                    )

                    accounts = new_followers if diff_type == "new_followers" else unfollowers

                    with VerticalScroll(classes="account-list"):
                        if not accounts:
                            empty_msg = self._get_empty_message(diff_type)
                            yield Static(empty_msg, classes="empty-list")
                        else:
                            for account in accounts:
                                yield self._create_account_widget(account)
                else:
                    # This is the first snapshot, no previous to compare
                    with VerticalScroll(classes="account-list"):
                        yield Static(
                            "This is your first snapshot.\n\n"
                            "Create another snapshot to see changes!",
                            classes="empty-list"
                        )

            except ValueError:
                with VerticalScroll(classes="account-list"):
                    yield Static("Snapshot not found.", classes="empty-list")

        except DatabaseError as e:
            with VerticalScroll(classes="account-list"):
                yield Static(f"Error loading accounts: {e}", classes="empty-list")

    def _create_account_widget(self, account: dict) -> Static:
        """Create a widget for displaying account information.

        Args:
            account: Account dictionary with username, display_name, url

        Returns:
            Static with formatted account info
        """
        username = f"@{account['username']}"
        display_name = account['display_name'] or ""
        # Pad username to 20 chars for alignment
        account_text = f"{username:<20} {display_name}"

        return Static(account_text, classes="account-row")

    def _get_empty_message(self, list_type: str) -> str:
        """Get appropriate empty message for each list type.

        Args:
            list_type: Type of list (relationship filter or diff type)

        Returns:
            Message to display when list is empty
        """
        messages = {
            "not_following_back": "Everyone you follow follows you back!",
            "not_followed_back": "You follow back everyone who follows you!",
            "new_followers": "No new followers since last snapshot.",
            "unfollowers": "No one unfollowed you since last snapshot.",
        }
        return messages.get(list_type, "No accounts found.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back-button":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Action to go back (keyboard shortcut)."""
        self.app.pop_screen()

    def action_tab_1(self) -> None:
        """Switch to tab 1."""
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "tab-1"

    def action_tab_2(self) -> None:
        """Switch to tab 2."""
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "tab-2"

    def action_tab_3(self) -> None:
        """Switch to tab 3."""
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "tab-3"

    def action_tab_4(self) -> None:
        """Switch to tab 4."""
        tabbed = self.query_one(TabbedContent)
        tabbed.active = "tab-4"

    def action_quit(self) -> None:
        """Action to quit (keyboard shortcut)."""
        self.app.exit()


class PettyApp(App):
    """A Textual app for tracking followers on federated social networks."""

    TITLE = "peTTY"
    SUB_TITLE = "Follower Tracker"

    CSS = """
    .screen-title {
        width: 100%;
        text-align: center;
        color: $accent;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        """Initialize app on mount."""
        # Initialize database
        initialize_database()

        # Check if config exists and has required credentials
        if not config_exists():
            # First time setup - show OAuth flow
            self.push_screen(OAuthSetupScreen())
        else:
            try:
                config = read_config()
                # Check if we have access token (complete setup)
                if not config.get("mastodon_access_token"):
                    # Incomplete setup - show OAuth flow
                    self.push_screen(OAuthSetupScreen())
                else:
                    # Config exists and is complete - show main menu
                    self.push_screen(MainMenuScreen())
            except ConfigError:
                # Config exists but is invalid - show OAuth flow
                self.push_screen(OAuthSetupScreen())


if __name__ == "__main__":
    app = PettyApp()
    app.run()
