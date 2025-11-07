"""Simple test script for database functionality."""

from src.petty.database import (
    initialize_database,
    create_snapshot,
    get_all_snapshots,
    get_snapshot_accounts,
    get_snapshot_diff,
    Account,
)


def main():
    """Test database operations."""
    print("Initializing database...")
    initialize_database()
    print("✓ Database initialized\n")

    # Create sample data
    followers = [
        Account(
            account_id="1",
            username="alice",
            display_name="Alice Wonder",
            url="https://mastodon.social/@alice",
        ),
        Account(
            account_id="2",
            username="bob",
            display_name="Bob Builder",
            url="https://mastodon.social/@bob",
        ),
        Account(
            account_id="3",
            username="charlie",
            display_name="Charlie Brown",
            url="https://mastodon.social/@charlie",
        ),
    ]

    following = [
        Account(
            account_id="2",
            username="bob",
            display_name="Bob Builder",
            url="https://mastodon.social/@bob",
        ),
        Account(
            account_id="4",
            username="diana",
            display_name="Diana Prince",
            url="https://mastodon.social/@diana",
        ),
    ]

    # Create first snapshot
    print("Creating first snapshot...")
    snapshot_id_1 = create_snapshot(followers, following)
    print(f"✓ Created snapshot {snapshot_id_1}\n")

    # Create second snapshot with changes
    print("Creating second snapshot with changes...")
    followers_2 = [
        Account(
            account_id="1",
            username="alice",
            display_name="Alice Wonder",
            url="https://mastodon.social/@alice",
        ),
        Account(
            account_id="2",
            username="bob",
            display_name="Bob Builder",
            url="https://mastodon.social/@bob",
        ),
        # charlie unfollowed
        Account(
            account_id="5",
            username="eve",
            display_name="Eve Online",
            url="https://mastodon.social/@eve",
        ),  # new follower
    ]

    snapshot_id_2 = create_snapshot(followers_2, following)
    print(f"✓ Created snapshot {snapshot_id_2}\n")

    # Test retrieving all snapshots
    print("Retrieving all snapshots...")
    snapshots = get_all_snapshots()
    for snapshot in snapshots:
        print(f"  Snapshot {snapshot['id']}: {snapshot['created_at']} "
              f"({snapshot['account_count']} accounts)")
    print()

    # Test retrieving accounts with filters
    print(f"Accounts in snapshot {snapshot_id_1}:")
    print("\n  Not following back:")
    not_following_back = get_snapshot_accounts(snapshot_id_1, "not_following_back")
    for acc in not_following_back:
        print(f"    @{acc['username']} ({acc['display_name']})")

    print("\n  Not followed back:")
    not_followed_back = get_snapshot_accounts(snapshot_id_1, "not_followed_back")
    for acc in not_followed_back:
        print(f"    @{acc['username']} ({acc['display_name']})")

    # Test snapshot diff
    print(f"\n\nComparing snapshots {snapshot_id_2} vs {snapshot_id_1}:")
    new_followers, unfollowers = get_snapshot_diff(snapshot_id_2, snapshot_id_1)

    print("\n  New followers:")
    for acc in new_followers:
        print(f"    @{acc['username']} ({acc['display_name']})")

    print("\n  Unfollowers:")
    for acc in unfollowers:
        print(f"    @{acc['username']} ({acc['display_name']})")

    print("\n✓ All tests completed successfully!")


if __name__ == "__main__":
    main()
