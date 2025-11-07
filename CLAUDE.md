# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses `uv` as the Python package manager:

- `uv sync` - Install/sync dependencies
- `uv run petty` - Run the application
- `uv run python test_database.py` - Run database test script
- `uv add <package>` - Add a dependency
- `uv build` - Build the package

## Architecture Overview

peTTY is a TUI application for tracking Mastodon followers, built with Textual. The architecture consists of three independent layers:

### Layer Structure

1. **UI Layer** (`app.py`)
   - Textual `App` subclass with TUI components
   - Currently minimal (welcome screen only)
   - Not yet integrated with other layers

2. **Configuration Layer** (`config.py`)
   - Manages `~/.config/petty/config.toml`
   - Required fields: `mastodon_server_url`, `mastodon_access_token`
   - Uses TypedDict for type safety
   - Custom `ConfigError` exception

3. **Database Layer** (`database.py`)
   - SQLite at `~/.config/petty/petty.db`
   - Two tables: `snapshots` and `snapshot_accounts`
   - Tracks bidirectional relationships: `is_follower` and `is_following` flags on each account
   - Supports snapshot comparison via `get_snapshot_diff()`
   - Custom `DatabaseError` exception

### Data Model

The database uses a snapshot-based versioning approach where each snapshot is immutable:

- **Snapshots** are timestamped records
- **Accounts** in each snapshot have both `is_follower` and `is_following` flags
- This allows querying for:
  - Who doesn't follow you back (`is_follower=1, is_following=0`)
  - Who you don't follow back (`is_follower=0, is_following=1`)
  - Changes between snapshots (new followers, unfollowers)

### Integration Points

The layers are currently independent. When integrating:

1. TUI should use `config.read_config()` to get Mastodon credentials
2. TUI should call Mastodon.py API to fetch follower/following data
3. TUI should use `database.create_snapshot()` to store data
4. TUI should use `database.get_snapshot_accounts()` and `database.get_snapshot_diff()` to display analyses

Required OAuth scopes: `read:accounts`, `read:follows`

## Code Conventions

- **TypedDict over dataclasses** - Used for config and database entities
- **Custom exceptions** - Raise `ConfigError` or `DatabaseError` with descriptive messages
- **pathlib.Path** - Used for all file operations
- **Context managers** - Database connections use `with get_connection()`
- **XDG compliance** - All data stored in `~/.config/petty/`
