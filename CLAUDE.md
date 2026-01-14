# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses `uv` as the Python package manager:

- `uv sync` - Install/sync dependencies
- `uv run petty` - Run the application
- `uv run python test_database.py` - Run database test script
- `uv run python test_mastodon_client.py` - Run Mastodon client test script
- `uv add <package>` - Add a dependency
- `uv build` - Build the package

## Architecture Overview

peTTY is a TUI application for tracking Mastodon followers, built with Textual. The architecture consists of four layers:

### Layer Structure

1. **UI Layer** (`app.py`)
   - `PettyApp`: Main Textual App that initializes database and routes to appropriate screen
   - `OAuthSetupScreen`: Multi-step OAuth flow with browser-based authorization
   - `MainMenuScreen`: Dashboard showing authenticated user and menu options
   - `CreateSnapshotScreen`: Async snapshot creation with progress updates
   - `ViewSnapshotsScreen`: List and manage snapshots
   - `SnapshotDetailScreen`: Four-tab analysis (not following back, not followed back, new followers, unfollowers)
   - Uses `@work` decorator for background I/O operations to keep UI responsive

2. **Configuration Layer** (`config.py`)
   - Manages `~/.config/petty/config.toml`
   - Fields: `mastodon_server_url`, `mastodon_access_token`, `client_id`, `client_secret`
   - Custom `ConfigError` exception

3. **Database Layer** (`database.py`)
   - SQLite at `~/.config/petty/petty.db`
   - Tables: `snapshots` and `snapshot_accounts` with foreign key cascade delete
   - Bidirectional relationship tracking: `is_follower` and `is_following` flags per account
   - Key functions: `create_snapshot()`, `get_snapshot_accounts()`, `get_snapshot_diff()`
   - Custom `DatabaseError` exception

4. **API Layer** (`mastodon_client.py`, `oauth.py`)
   - `mastodon_client.py`: Wrapper around Mastodon.py for fetching followers/following
   - `oauth.py`: OAuth 2.0 out-of-band flow with scopes `read:accounts`, `read:follows`
   - Custom `MastodonClientError` and `OAuthError` exceptions

### Data Model

Snapshots are immutable timestamped records. Each account in a snapshot has:
- `is_follower`: True if they follow you
- `is_following`: True if you follow them

This enables queries like "who doesn't follow back" and diff comparisons between snapshots.

## Code Conventions

- **TypedDict over dataclasses** - All data models (Config, Account, Snapshot, etc.)
- **Custom exceptions per layer** - `ConfigError`, `DatabaseError`, `MastodonClientError`, `OAuthError`
- **pathlib.Path** - All file operations
- **Context managers** - Database connections via `with get_connection()`
- **XDG compliance** - All data in `~/.config/petty/`
- **Worker threads** - Textual `@work` decorator for API calls and DB operations
