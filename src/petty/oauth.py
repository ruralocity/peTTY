"""OAuth authentication flow for Mastodon."""

import webbrowser
from typing import Tuple

from mastodon import Mastodon, MastodonError

from .config import Config, write_config, ConfigError


class OAuthError(Exception):
    """Raised when there's an issue with OAuth flow."""

    pass


APP_NAME = "peTTY"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"  # Out-of-band for CLI apps
SCOPES = ["read:accounts", "read:follows"]


def register_app(server_url: str) -> Tuple[str, str]:
    """Register peTTY as an app with the Mastodon server.

    Args:
        server_url: The Mastodon server URL (e.g., https://mastodon.social)

    Returns:
        Tuple of (client_id, client_secret)

    Raises:
        OAuthError: If registration fails
    """
    try:
        client_id, client_secret = Mastodon.create_app(
            APP_NAME,
            api_base_url=server_url,
            redirect_uris=REDIRECT_URI,
            scopes=SCOPES,
        )
        return str(client_id), str(client_secret)
    except MastodonError as e:
        raise OAuthError(f"Failed to register app with {server_url}: {e}")
    except Exception as e:
        raise OAuthError(f"Unexpected error during app registration: {e}")


def get_authorization_url(server_url: str, client_id: str, client_secret: str) -> str:
    """Generate the OAuth authorization URL for the user to visit.

    Args:
        server_url: The Mastodon server URL
        client_id: The app's client ID
        client_secret: The app's client secret

    Returns:
        Authorization URL for the user to visit

    Raises:
        OAuthError: If unable to generate URL
    """
    try:
        client = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            api_base_url=server_url,
        )
        auth_url = client.auth_request_url(
            redirect_uris=REDIRECT_URI,
            scopes=SCOPES,
        )
        return str(auth_url)
    except MastodonError as e:
        raise OAuthError(f"Failed to generate authorization URL: {e}")
    except Exception as e:
        raise OAuthError(f"Unexpected error generating authorization URL: {e}")


def open_browser(url: str) -> bool:
    """Attempt to open the authorization URL in the user's browser.

    Args:
        url: The URL to open

    Returns:
        True if browser opened successfully, False otherwise
    """
    try:
        return webbrowser.open(url)
    except Exception:
        return False


def exchange_code_for_token(
    server_url: str, client_id: str, client_secret: str, auth_code: str
) -> str:
    """Exchange the authorization code for an access token.

    Args:
        server_url: The Mastodon server URL
        client_id: The app's client ID
        client_secret: The app's client secret
        auth_code: The authorization code from the user

    Returns:
        Access token string

    Raises:
        OAuthError: If exchange fails
    """
    try:
        client = Mastodon(
            client_id=client_id,
            client_secret=client_secret,
            api_base_url=server_url,
        )

        access_token = client.log_in(
            code=auth_code,
            redirect_uri=REDIRECT_URI,
            scopes=SCOPES,
        )

        return str(access_token)
    except MastodonError as e:
        raise OAuthError(f"Failed to exchange authorization code: {e}")
    except Exception as e:
        raise OAuthError(f"Unexpected error during token exchange: {e}")


def complete_oauth_setup(
    server_url: str, client_id: str, client_secret: str, access_token: str
) -> None:
    """Save OAuth credentials to config file.

    Args:
        server_url: The Mastodon server URL
        client_id: The app's client ID
        client_secret: The app's client secret
        access_token: The user's access token

    Raises:
        ConfigError: If unable to save config
    """
    config = Config(
        mastodon_server_url=server_url,
        client_id=client_id,
        client_secret=client_secret,
        mastodon_access_token=access_token,
    )

    write_config(config)


def run_oauth_flow(server_url: str) -> Config:
    """Run the complete OAuth flow and return the config.

    Args:
        server_url: The Mastodon server URL

    Returns:
        Complete config with OAuth credentials

    Raises:
        OAuthError: If any step of the OAuth flow fails
    """
    # Step 1: Register the app
    client_id, client_secret = register_app(server_url)

    # Step 2: Get authorization URL
    auth_url = get_authorization_url(server_url, client_id)

    # Return partial config with auth_url for the UI to handle
    # The UI will need to:
    # 1. Show the auth_url to the user
    # 2. Get the authorization code from the user
    # 3. Call exchange_code_for_token
    # 4. Call complete_oauth_setup
    raise NotImplementedError(
        "This function should be used by the UI, not called directly. "
        "Use register_app, get_authorization_url, and exchange_code_for_token separately."
    )
