"""Database management for peTTY snapshots."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, TypedDict


class Account(TypedDict):
    """Represents a Mastodon account."""

    account_id: str
    username: str
    display_name: str
    url: str


class SnapshotAccount(Account):
    """Account with relationship information."""

    is_follower: bool
    is_following: bool


class Snapshot(TypedDict):
    """Represents a snapshot of follower data."""

    id: int
    created_at: str
    account_count: int


class DatabaseError(Exception):
    """Raised when there's an issue with the database."""

    pass


def get_database_path() -> Path:
    """Get the path to the database file.

    Returns:
        Path to database file at ~/.config/petty/petty.db
    """
    config_dir = Path.home() / ".config" / "petty"
    return config_dir / "petty.db"


def ensure_database_dir() -> None:
    """Create the database directory if it doesn't exist."""
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Get a connection to the database.

    Returns:
        SQLite connection object

    Raises:
        DatabaseError: If unable to connect to database
    """
    try:
        ensure_database_dir()
        conn = sqlite3.connect(get_database_path())
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to connect to database: {e}")


def initialize_database() -> None:
    """Initialize the database schema.

    Creates the necessary tables if they don't exist.

    Raises:
        DatabaseError: If unable to initialize database
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL
                )
            """)

            # Create snapshot_accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshot_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    account_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    is_follower BOOLEAN NOT NULL,
                    is_following BOOLEAN NOT NULL,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots (id) ON DELETE CASCADE
                )
            """)

            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshot_accounts_snapshot_id
                ON snapshot_accounts (snapshot_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshot_accounts_account_id
                ON snapshot_accounts (account_id)
            """)

            conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to initialize database: {e}")


def create_snapshot(
    followers: List[Account], following: List[Account]
) -> int:
    """Create a new snapshot with follower and following data.

    Args:
        followers: List of accounts that follow the user
        following: List of accounts that the user follows

    Returns:
        ID of the created snapshot

    Raises:
        DatabaseError: If unable to create snapshot
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Create snapshot record
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO snapshots (created_at) VALUES (?)", (now,)
            )
            snapshot_id = cursor.lastrowid

            # Create sets for efficient lookup
            follower_ids = {acc["account_id"] for acc in followers}
            following_ids = {acc["account_id"] for acc in following}

            # Combine all accounts
            all_accounts = {}
            for acc in followers:
                all_accounts[acc["account_id"]] = acc

            for acc in following:
                if acc["account_id"] not in all_accounts:
                    all_accounts[acc["account_id"]] = acc

            # Insert account records
            for account_id, account in all_accounts.items():
                cursor.execute(
                    """
                    INSERT INTO snapshot_accounts
                    (snapshot_id, account_id, username, display_name, url,
                     is_follower, is_following)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_id,
                        account_id,
                        account["username"],
                        account["display_name"],
                        account["url"],
                        account_id in follower_ids,
                        account_id in following_ids,
                    ),
                )

            conn.commit()
            return snapshot_id
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to create snapshot: {e}")


def get_all_snapshots() -> List[Snapshot]:
    """Get a list of all snapshots.

    Returns:
        List of snapshots with basic information

    Raises:
        DatabaseError: If unable to retrieve snapshots
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    s.id,
                    s.created_at,
                    COUNT(sa.id) as account_count
                FROM snapshots s
                LEFT JOIN snapshot_accounts sa ON s.id = sa.snapshot_id
                GROUP BY s.id
                ORDER BY s.created_at DESC
            """)

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append(
                    Snapshot(
                        id=row["id"],
                        created_at=row["created_at"],
                        account_count=row["account_count"],
                    )
                )

            return snapshots
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to retrieve snapshots: {e}")


def get_snapshot_accounts(
    snapshot_id: int, relationship_filter: Optional[str] = None
) -> List[SnapshotAccount]:
    """Get accounts from a snapshot with optional filtering.

    Args:
        snapshot_id: ID of the snapshot
        relationship_filter: Optional filter - 'followers', 'following',
                           'not_following_back', 'not_followed_back'

    Returns:
        List of accounts matching the filter criteria

    Raises:
        DatabaseError: If unable to retrieve accounts
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build query based on filter
            query = """
                SELECT account_id, username, display_name, url,
                       is_follower, is_following
                FROM snapshot_accounts
                WHERE snapshot_id = ?
            """

            if relationship_filter == "followers":
                query += " AND is_follower = 1"
            elif relationship_filter == "following":
                query += " AND is_following = 1"
            elif relationship_filter == "not_following_back":
                # They follow me, but I don't follow them
                query += " AND is_follower = 1 AND is_following = 0"
            elif relationship_filter == "not_followed_back":
                # I follow them, but they don't follow me
                query += " AND is_following = 1 AND is_follower = 0"

            query += " ORDER BY username"

            cursor.execute(query, (snapshot_id,))

            accounts = []
            for row in cursor.fetchall():
                accounts.append(
                    SnapshotAccount(
                        account_id=row["account_id"],
                        username=row["username"],
                        display_name=row["display_name"],
                        url=row["url"],
                        is_follower=bool(row["is_follower"]),
                        is_following=bool(row["is_following"]),
                    )
                )

            return accounts
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to retrieve snapshot accounts: {e}")


def get_snapshot_diff(
    current_snapshot_id: int, previous_snapshot_id: int
) -> tuple[List[SnapshotAccount], List[SnapshotAccount]]:
    """Compare two snapshots to find new followers and unfollowers.

    Args:
        current_snapshot_id: ID of the current snapshot
        previous_snapshot_id: ID of the previous snapshot

    Returns:
        Tuple of (new_followers, unfollowers)

    Raises:
        DatabaseError: If unable to compute diff
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Find new followers (in current but not in previous)
            cursor.execute(
                """
                SELECT DISTINCT c.account_id, c.username, c.display_name,
                       c.url, c.is_follower, c.is_following
                FROM snapshot_accounts c
                WHERE c.snapshot_id = ? AND c.is_follower = 1
                AND c.account_id NOT IN (
                    SELECT p.account_id
                    FROM snapshot_accounts p
                    WHERE p.snapshot_id = ? AND p.is_follower = 1
                )
                ORDER BY c.username
                """,
                (current_snapshot_id, previous_snapshot_id),
            )

            new_followers = []
            for row in cursor.fetchall():
                new_followers.append(
                    SnapshotAccount(
                        account_id=row["account_id"],
                        username=row["username"],
                        display_name=row["display_name"],
                        url=row["url"],
                        is_follower=bool(row["is_follower"]),
                        is_following=bool(row["is_following"]),
                    )
                )

            # Find unfollowers (in previous but not in current)
            cursor.execute(
                """
                SELECT DISTINCT p.account_id, p.username, p.display_name,
                       p.url, p.is_follower, p.is_following
                FROM snapshot_accounts p
                WHERE p.snapshot_id = ? AND p.is_follower = 1
                AND p.account_id NOT IN (
                    SELECT c.account_id
                    FROM snapshot_accounts c
                    WHERE c.snapshot_id = ? AND c.is_follower = 1
                )
                ORDER BY p.username
                """,
                (previous_snapshot_id, current_snapshot_id),
            )

            unfollowers = []
            for row in cursor.fetchall():
                unfollowers.append(
                    SnapshotAccount(
                        account_id=row["account_id"],
                        username=row["username"],
                        display_name=row["display_name"],
                        url=row["url"],
                        is_follower=bool(row["is_follower"]),
                        is_following=bool(row["is_following"]),
                    )
                )

            return (new_followers, unfollowers)
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to compute snapshot diff: {e}")


def delete_snapshot(snapshot_id: int) -> None:
    """Delete a snapshot and all associated account records.

    Args:
        snapshot_id: ID of the snapshot to delete

    Raises:
        DatabaseError: If unable to delete snapshot
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
            conn.commit()
    except sqlite3.Error as e:
        raise DatabaseError(f"Failed to delete snapshot: {e}")
