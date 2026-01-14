# UI Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make peTTY's UI consistent across screens and more intuitive to navigate.

**Architecture:** All changes are in `src/petty/app.py`. We'll update CSS rules for visual consistency, BINDINGS for navigation, and refactor SnapshotDetailScreen's account list rendering.

**Tech Stack:** Textual TUI framework, Python

---

## Task 1: Standardize Container Widths

**Files:**
- Modify: `src/petty/app.py` (CSS blocks in each Screen class)

**Step 1: Update OAuthSetupScreen container width**

In `OAuthSetupScreen.CSS`, change:
```css
#setup-container {
    width: 80;
```
to:
```css
#setup-container {
    width: 90%;
```

**Step 2: Update MainMenuScreen container width**

In `MainMenuScreen.CSS`, change:
```css
#menu-container {
    width: 70;
```
to:
```css
#menu-container {
    width: 90%;
```

**Step 3: Update CreateSnapshotScreen container width**

In `CreateSnapshotScreen.CSS`, change:
```css
#snapshot-container {
    width: 70;
```
to:
```css
#snapshot-container {
    width: 90%;
```

**Step 4: Update ViewSnapshotsScreen container width**

In `ViewSnapshotsScreen.CSS`, change:
```css
#snapshots-container {
    width: 80;
```
to:
```css
#snapshots-container {
    width: 90%;
```

**Step 5: Verify SnapshotDetailScreen (already 90%)**

Confirm `#detail-container` already has `width: 90%;` - no change needed.

**Step 6: Run app to verify visually**

Run: `uv run petty`
Expected: All screens should now use consistent 90% width.

**Step 7: Commit**

```bash
git add src/petty/app.py
git commit -m "Standardize container widths to 90%"
```

---

## Task 2: Standardize Title Styling

**Files:**
- Modify: `src/petty/app.py` (CSS and compose methods)

**Step 1: Add shared title class to OAuthSetupScreen**

Already has `.setup-title` with good styling. Keep as reference:
```css
.setup-title {
    width: 100%;
    text-align: center;
    color: $accent;
    margin-bottom: 1;
}
```

**Step 2: Add title styling to MainMenuScreen CSS**

Add to `MainMenuScreen.CSS`:
```css
.screen-title {
    width: 100%;
    text-align: center;
    color: $accent;
    margin-bottom: 1;
}
```

**Step 3: Update MainMenuScreen compose to use styled title**

Change:
```python
yield Static("peTTY - Mastodon Follower Tracker", classes="title")
```
to:
```python
yield Static("peTTY - Mastodon Follower Tracker", classes="screen-title")
```

**Step 4: Add title styling to CreateSnapshotScreen CSS**

Add to `CreateSnapshotScreen.CSS`:
```css
.screen-title {
    width: 100%;
    text-align: center;
    color: $accent;
    margin-bottom: 1;
}
```

**Step 5: Update CreateSnapshotScreen compose to use styled title**

Change:
```python
yield Label("Create New Snapshot", id="title")
```
to:
```python
yield Static("Create New Snapshot", classes="screen-title")
```

**Step 6: Add title styling to ViewSnapshotsScreen CSS**

Add to `ViewSnapshotsScreen.CSS`:
```css
.screen-title {
    width: 100%;
    text-align: center;
    color: $accent;
    margin-bottom: 1;
}
```

**Step 7: Update ViewSnapshotsScreen compose to use styled title**

Change:
```python
yield Label("Your Snapshots", id="title")
```
to:
```python
yield Static("Your Snapshots", classes="screen-title")
```

**Step 8: Add title styling to SnapshotDetailScreen CSS**

The `#snapshot-header` already has some styling. Update to match:
```css
#snapshot-header {
    width: 100%;
    height: auto;
    text-align: center;
    color: $accent;
    margin-bottom: 1;
    padding: 1;
    background: $boost;
}
```
This keeps the background but adds accent color for consistency.

**Step 9: Run app to verify visually**

Run: `uv run petty`
Expected: All screen titles should be centered with accent color.

**Step 10: Commit**

```bash
git add src/petty/app.py
git commit -m "Standardize title styling across screens"
```

---

## Task 3: Standardize Button Styling

**Files:**
- Modify: `src/petty/app.py` (CSS and compose methods)

**Step 1: Update MainMenuScreen button CSS**

Change the Button CSS in `MainMenuScreen.CSS` from:
```css
Button {
    width: 100%;
    margin: 1 0;
}
```
to:
```css
Button {
    margin: 0 1;
}
```

**Step 2: Update MainMenuScreen button container**

Change `.menu-buttons` from `Vertical` to `Horizontal` and update CSS:
```css
.menu-buttons {
    width: 100%;
    height: auto;
    align: center middle;
    margin-top: 1;
}
```

In compose, change:
```python
with Vertical(classes="menu-buttons"):
```
to:
```python
with Horizontal(classes="menu-buttons"):
```

**Step 3: Update ViewSnapshotsScreen button variants**

The buttons already use correct variants. Verify:
- "View Details" has `variant="primary"` ✓
- "Delete" has `variant="error"` ✓
- "Back to Menu" has `variant="default"` ✓

**Step 4: Run app to verify visually**

Run: `uv run petty`
Expected: MainMenuScreen buttons should be horizontal and centered.

**Step 5: Commit**

```bash
git add src/petty/app.py
git commit -m "Standardize button styling (horizontal, centered)"
```

---

## Task 4: Standardize Container Padding

**Files:**
- Modify: `src/petty/app.py` (CSS blocks)

**Step 1: Update OAuthSetupScreen padding**

In `OAuthSetupScreen.CSS`, change:
```css
#setup-container {
    width: 90%;
    height: auto;
    border: thick $primary;
    padding: 2;
}
```
to:
```css
#setup-container {
    width: 90%;
    height: auto;
    border: thick $primary;
    padding: 1 2;
}
```

**Step 2: Update CreateSnapshotScreen padding**

In `CreateSnapshotScreen.CSS`, change:
```css
#snapshot-container {
    width: 90%;
    height: auto;
    border: thick $primary;
    padding: 2;
}
```
to:
```css
#snapshot-container {
    width: 90%;
    height: auto;
    border: thick $primary;
    padding: 1 2;
}
```

**Step 3: Verify other screens (already correct)**

- MainMenuScreen: `padding: 1 2;` ✓
- ViewSnapshotsScreen: `padding: 1 2;` ✓
- SnapshotDetailScreen: `padding: 1 2;` ✓

**Step 4: Run app to verify visually**

Run: `uv run petty`
Expected: Consistent padding across all screens.

**Step 5: Commit**

```bash
git add src/petty/app.py
git commit -m "Standardize container padding to 1 2"
```

---

## Task 5: Update Navigation Bindings - MainMenuScreen

**Files:**
- Modify: `src/petty/app.py` (MainMenuScreen.BINDINGS)

**Step 1: Update MainMenuScreen BINDINGS**

Change:
```python
BINDINGS = [
    ("c", "create_snapshot", "Create Snapshot"),
    ("v", "view_snapshots", "View Snapshots"),
    ("q", "quit", "Quit"),
]
```
to:
```python
BINDINGS = [
    ("c", "create_snapshot", "Create Snapshot"),
    ("v", "view_snapshots", "View Snapshots"),
    ("q", "quit", "Quit"),
]
```
(No change needed - already correct per design. Escape is not bound, which means it does nothing.)

**Step 2: Run app to verify**

Run: `uv run petty`
Expected: On MainMenuScreen, pressing Escape does nothing. `q` quits.

**Step 3: Commit (skip if no changes)**

No commit needed for this task.

---

## Task 6: Update Navigation Bindings - CreateSnapshotScreen

**Files:**
- Modify: `src/petty/app.py` (CreateSnapshotScreen.BINDINGS)

**Step 1: Update CreateSnapshotScreen BINDINGS**

Change:
```python
BINDINGS = [
    ("escape", "back", "Back"),
]
```
to:
```python
BINDINGS = [
    ("escape", "back", "Back"),
    ("q", "quit", "Quit"),
]
```

**Step 2: Add quit action to CreateSnapshotScreen**

Add method:
```python
def action_quit(self) -> None:
    """Action to quit (keyboard shortcut)."""
    self.app.exit()
```

**Step 3: Run app to verify**

Run: `uv run petty`
Expected: On CreateSnapshotScreen, Escape goes back, `q` quits.

**Step 4: Commit**

```bash
git add src/petty/app.py
git commit -m "Add quit binding to CreateSnapshotScreen"
```

---

## Task 7: Update Navigation Bindings - ViewSnapshotsScreen

**Files:**
- Modify: `src/petty/app.py` (ViewSnapshotsScreen.BINDINGS)

**Step 1: Update ViewSnapshotsScreen BINDINGS**

Change:
```python
BINDINGS = [
    ("escape", "back", "Back"),
    ("enter", "view_selected", "View Details"),
    ("d", "delete_selected", "Delete"),
]
```
to:
```python
BINDINGS = [
    ("escape", "back", "Back"),
    ("enter", "view_selected", "View"),
    ("d", "delete_selected", "Delete"),
    ("q", "quit", "Quit"),
]
```

**Step 2: Add quit action to ViewSnapshotsScreen**

Add method:
```python
def action_quit(self) -> None:
    """Action to quit (keyboard shortcut)."""
    self.app.exit()
```

**Step 3: Run app to verify**

Run: `uv run petty`
Expected: On ViewSnapshotsScreen, footer shows all bindings including `q Quit`.

**Step 4: Commit**

```bash
git add src/petty/app.py
git commit -m "Add quit binding to ViewSnapshotsScreen"
```

---

## Task 8: Update Navigation Bindings - SnapshotDetailScreen

**Files:**
- Modify: `src/petty/app.py` (SnapshotDetailScreen.BINDINGS)

**Step 1: Update SnapshotDetailScreen BINDINGS**

Change:
```python
BINDINGS = [
    ("escape", "back", "Back"),
    ("1", "tab_1", "Not Following Back"),
    ("2", "tab_2", "Not Followed Back"),
    ("3", "tab_3", "New Followers"),
    ("4", "tab_4", "Unfollowers"),
]
```
to:
```python
BINDINGS = [
    ("escape", "back", "Back"),
    ("1", "tab_1", "Tab 1"),
    ("2", "tab_2", "Tab 2"),
    ("3", "tab_3", "Tab 3"),
    ("4", "tab_4", "Tab 4"),
    ("q", "quit", "Quit"),
]
```

Note: Shortened tab names to reduce footer clutter. The tab content headers will show full names.

**Step 2: Add quit action to SnapshotDetailScreen**

Add method:
```python
def action_quit(self) -> None:
    """Action to quit (keyboard shortcut)."""
    self.app.exit()
```

**Step 3: Run app to verify**

Run: `uv run petty`
Expected: On SnapshotDetailScreen, footer shows bindings including `q Quit`.

**Step 4: Commit**

```bash
git add src/petty/app.py
git commit -m "Add quit binding to SnapshotDetailScreen"
```

---

## Task 9: Update Navigation Bindings - OAuthSetupScreen

**Files:**
- Modify: `src/petty/app.py` (OAuthSetupScreen.BINDINGS)

**Step 1: Verify OAuthSetupScreen BINDINGS**

Current:
```python
BINDINGS = [
    ("escape", "quit", "Quit"),
]
```

This is correct per design - Escape quits during OAuth setup since there's no back destination.

**Step 2: Commit (skip if no changes)**

No commit needed for this task.

---

## Task 10: Rename Back Button Labels

**Files:**
- Modify: `src/petty/app.py` (compose methods)

**Step 1: Update CreateSnapshotScreen back button**

Change:
```python
yield Button("Back to Menu", id="back-button", variant="default")
```
to:
```python
yield Button("Back", id="back-button", variant="default")
```

**Step 2: Update ViewSnapshotsScreen back button**

Change:
```python
yield Button("Back to Menu", id="back-button", variant="default")
```
to:
```python
yield Button("Back", id="back-button", variant="default")
```

**Step 3: Update SnapshotDetailScreen back button**

Change:
```python
yield Button("Back to List", id="back-button", variant="default")
```
to:
```python
yield Button("Back", id="back-button", variant="default")
```

**Step 4: Run app to verify**

Run: `uv run petty`
Expected: All back buttons now say "Back".

**Step 5: Commit**

```bash
git add src/petty/app.py
git commit -m "Simplify back button labels to just Back"
```

---

## Task 11: Refactor SnapshotDetailScreen Account Lists - CSS

**Files:**
- Modify: `src/petty/app.py` (SnapshotDetailScreen.CSS)

**Step 1: Update account list CSS**

Replace the account-related CSS in `SnapshotDetailScreen.CSS`:

Remove:
```css
.account-item {
    width: 100%;
    padding: 1;
    margin: 0 0 1 0;
    border: solid $panel;
    background: $surface;
}

.account-username {
    color: $accent;
}

.account-display-name {
    color: $text;
}

.account-url {
    color: $text-muted;
}
```

Add:
```css
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
```

**Step 2: Commit**

```bash
git add src/petty/app.py
git commit -m "Update SnapshotDetailScreen CSS for compact table format"
```

---

## Task 12: Refactor SnapshotDetailScreen Account Lists - Header Component

**Files:**
- Modify: `src/petty/app.py` (SnapshotDetailScreen methods)

**Step 1: Add method to create list header**

Add new method to SnapshotDetailScreen:
```python
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
```

**Step 2: Commit**

```bash
git add src/petty/app.py
git commit -m "Add list header component for SnapshotDetailScreen"
```

---

## Task 13: Refactor SnapshotDetailScreen Account Lists - Table Rendering

**Files:**
- Modify: `src/petty/app.py` (SnapshotDetailScreen._create_account_widget)

**Step 1: Update _create_account_widget for table format**

Change:
```python
def _create_account_widget(self, account: dict) -> Container:
    """Create a widget for displaying account information.

    Args:
        account: Account dictionary with username, display_name, url

    Returns:
        Container with formatted account info
    """
    account_text = (
        f"[bold]@{account['username']}[/bold]\n"
        f"{account['display_name']}\n"
        f"[dim]{account['url']}[/dim]"
    )

    return Static(account_text, classes="account-item", markup=True)
```
to:
```python
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
```

**Step 2: Commit**

```bash
git add src/petty/app.py
git commit -m "Update account widget for compact table format"
```

---

## Task 14: Refactor SnapshotDetailScreen Account Lists - Update _create_account_list

**Files:**
- Modify: `src/petty/app.py` (SnapshotDetailScreen._create_account_list)

**Step 1: Update _create_account_list to use header**

Change:
```python
def _create_account_list(self, relationship_filter: str) -> ComposeResult:
    """Create a scrollable list of accounts.

    Args:
        relationship_filter: Filter type for get_snapshot_accounts

    Returns:
        Generator yielding VerticalScroll with account items
    """
    try:
        accounts = get_snapshot_accounts(self.snapshot_id, relationship_filter)

        with VerticalScroll(classes="account-list"):
            if not accounts:
                empty_msg = self._get_empty_message(relationship_filter)
                yield Static(empty_msg, classes="empty-list")
            else:
                for account in accounts:
                    yield self._create_account_widget(account)

    except DatabaseError as e:
        with VerticalScroll(classes="account-list"):
            yield Static(f"Error loading accounts: {e}", classes="empty-list")
```
to:
```python
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
```

**Step 2: Add _get_list_title helper method**

Add new method:
```python
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
```

**Step 3: Commit**

```bash
git add src/petty/app.py
git commit -m "Update _create_account_list to use header with count"
```

---

## Task 15: Refactor SnapshotDetailScreen Account Lists - Update _create_diff_list

**Files:**
- Modify: `src/petty/app.py` (SnapshotDetailScreen._create_diff_list)

**Step 1: Update _create_diff_list to use header**

Replace the method to use the new header pattern:
```python
def _create_diff_list(self, diff_type: str) -> ComposeResult:
    """Create a scrollable list showing diff between snapshots.

    Args:
        diff_type: Either 'new_followers' or 'unfollowers'

    Returns:
        Generator yielding VerticalScroll with account items
    """
    title = self._get_list_title(diff_type)

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
                        yield from self._create_list_header(title, 0)
                        empty_msg = self._get_empty_message(diff_type)
                        yield Static(empty_msg, classes="empty-list")
                    else:
                        yield from self._create_list_header(title, len(accounts))
                        for account in accounts:
                            yield self._create_account_widget(account)
            else:
                # This is the first snapshot, no previous to compare
                with VerticalScroll(classes="account-list"):
                    yield from self._create_list_header(title, 0)
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
```

**Step 2: Run app to verify**

Run: `uv run petty`
Expected: SnapshotDetailScreen tabs show compact table format with headers.

**Step 3: Commit**

```bash
git add src/petty/app.py
git commit -m "Update _create_diff_list to use header with count"
```

---

## Task 16: Final Verification

**Step 1: Run full app test**

Run: `uv run petty`

Verify:
- [ ] All screens use 90% width
- [ ] All titles are centered with accent color
- [ ] MainMenuScreen buttons are horizontal and centered
- [ ] Escape goes back on all screens (does nothing on MainMenuScreen)
- [ ] `q` quits from any screen
- [ ] All back buttons say "Back"
- [ ] SnapshotDetailScreen shows compact table format with headers

**Step 2: Commit any final fixes if needed**

**Step 3: Final commit message**

If all looks good, no additional commit needed. The implementation is complete.
