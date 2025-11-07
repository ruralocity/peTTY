"""Test script for Mastodon API client integration."""

from src.petty.config import read_config, ConfigError
from src.petty.mastodon_client import (
    create_client,
    verify_credentials,
    fetch_followers,
    fetch_following,
    MastodonClientError,
)


def main():
    """Test Mastodon client functionality."""
    print("Testing Mastodon API client...\n")

    # Load configuration
    try:
        print("Loading configuration...")
        config = read_config()
        print(f"✓ Config loaded from {config['mastodon_server_url']}\n")
    except ConfigError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease set up your config file at ~/.config/petty/config.toml")
        print("See README.md for instructions.")
        return

    # Create client
    try:
        print("Creating Mastodon client...")
        client = create_client(config)
        print("✓ Client created\n")
    except MastodonClientError as e:
        print(f"✗ Failed to create client: {e}")
        return

    # Verify credentials
    try:
        print("Verifying credentials...")
        user_info = verify_credentials(client)
        print(f"✓ Authenticated as: @{user_info['username']}")
        print(f"  Display name: {user_info['display_name']}")
        print(f"  Followers: {user_info['followers_count']}")
        print(f"  Following: {user_info['following_count']}")
        print(f"  URL: {user_info['url']}\n")
    except MastodonClientError as e:
        print(f"✗ Failed to verify credentials: {e}")
        return

    # Fetch followers
    try:
        print("Fetching followers...")
        followers = fetch_followers(client)
        print(f"✓ Fetched {len(followers)} followers")
        if followers:
            print(f"  Examples:")
            for follower in followers[:3]:
                print(f"    @{follower['username']} - {follower['display_name']}")
        print()
    except MastodonClientError as e:
        print(f"✗ Failed to fetch followers: {e}\n")

    # Fetch following
    try:
        print("Fetching following...")
        following = fetch_following(client)
        print(f"✓ Fetched {len(following)} following")
        if following:
            print(f"  Examples:")
            for account in following[:3]:
                print(f"    @{account['username']} - {account['display_name']}")
        print()
    except MastodonClientError as e:
        print(f"✗ Failed to fetch following: {e}\n")

    print("✓ All tests completed successfully!")


if __name__ == "__main__":
    main()
