"""Mastodon API client integration for peTTY."""

from typing import List

from mastodon import Mastodon, MastodonError

from .config import Config
from .database import Account


class MastodonClientError(Exception):
    """Raised when there's an issue with the Mastodon API client."""

    pass


def create_client(config: Config) -> Mastodon:
    """Create a Mastodon API client from configuration.

    Args:
        config: Configuration with server URL and access token

    Returns:
        Initialized Mastodon client

    Raises:
        MastodonClientError: If unable to create client
    """
    try:
        client = Mastodon(
            access_token=config["mastodon_access_token"],
            api_base_url=config["mastodon_server_url"],
        )
        return client
    except Exception as e:
        raise MastodonClientError(f"Failed to create Mastodon client: {e}")


def _convert_mastodon_account(account: dict) -> Account:
    """Convert a Mastodon account dict to our Account TypedDict.

    Args:
        account: Account dict from Mastodon API

    Returns:
        Account TypedDict with required fields
    """
    return Account(
        account_id=str(account["id"]),
        username=account["username"],
        display_name=account["display_name"] or account["username"],
        url=account["url"],
    )


def fetch_followers(client: Mastodon) -> List[Account]:
    """Fetch all followers for the authenticated user.

    Args:
        client: Initialized Mastodon client

    Returns:
        List of follower accounts

    Raises:
        MastodonClientError: If unable to fetch followers
    """
    try:
        # Get the authenticated user's account
        me = client.me()
        user_id = me["id"]

        # Fetch all followers (handles pagination automatically)
        followers_data = client.fetch_remaining(
            client.account_followers(user_id)
        )

        # Convert to our Account format
        followers = [_convert_mastodon_account(acc) for acc in followers_data]

        return followers
    except MastodonError as e:
        raise MastodonClientError(f"Failed to fetch followers: {e}")
    except Exception as e:
        raise MastodonClientError(f"Unexpected error fetching followers: {e}")


def fetch_following(client: Mastodon) -> List[Account]:
    """Fetch all accounts the authenticated user is following.

    Args:
        client: Initialized Mastodon client

    Returns:
        List of following accounts

    Raises:
        MastodonClientError: If unable to fetch following list
    """
    try:
        # Get the authenticated user's account
        me = client.me()
        user_id = me["id"]

        # Fetch all following (handles pagination automatically)
        following_data = client.fetch_remaining(
            client.account_following(user_id)
        )

        # Convert to our Account format
        following = [_convert_mastodon_account(acc) for acc in following_data]

        return following
    except MastodonError as e:
        raise MastodonClientError(f"Failed to fetch following list: {e}")
    except Exception as e:
        raise MastodonClientError(f"Unexpected error fetching following: {e}")


def verify_credentials(client: Mastodon) -> dict:
    """Verify the credentials and get authenticated user info.

    Args:
        client: Initialized Mastodon client

    Returns:
        Dict with user information (id, username, display_name, url)

    Raises:
        MastodonClientError: If credentials are invalid
    """
    try:
        me = client.me()
        return {
            "id": str(me["id"]),
            "username": me["username"],
            "display_name": me["display_name"] or me["username"],
            "url": me["url"],
            "followers_count": me.get("followers_count", 0),
            "following_count": me.get("following_count", 0),
        }
    except MastodonError as e:
        raise MastodonClientError(f"Failed to verify credentials: {e}")
    except Exception as e:
        raise MastodonClientError(f"Unexpected error verifying credentials: {e}")
