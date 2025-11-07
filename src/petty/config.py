"""Configuration management for peTTY."""

import tomllib
from pathlib import Path
from typing import TypedDict

import tomli_w


class Config(TypedDict, total=False):
    """Configuration structure for peTTY.

    Note: total=False makes all fields optional for TypedDict,
    but we validate required fields at runtime.
    """

    mastodon_server_url: str
    mastodon_access_token: str
    client_id: str
    client_secret: str


class ConfigError(Exception):
    """Raised when there's an issue with configuration."""

    pass


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to config file at ~/.config/petty/config.toml
    """
    config_dir = Path.home() / ".config" / "petty"
    return config_dir / "config.toml"


def get_config_dir() -> Path:
    """Get the configuration directory path.

    Returns:
        Path to config directory at ~/.config/petty
    """
    return Path.home() / ".config" / "petty"


def ensure_config_dir() -> None:
    """Create the configuration directory if it doesn't exist."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def config_exists() -> bool:
    """Check if configuration file exists.

    Returns:
        True if config file exists, False otherwise
    """
    return get_config_path().exists()


def read_config() -> Config:
    """Read and parse the configuration file.

    Returns:
        Parsed configuration dictionary

    Raises:
        ConfigError: If config file doesn't exist or is invalid
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise ConfigError(
            f"Configuration file not found at {config_path}. "
            "Please run the OAuth setup to configure peTTY."
        )

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in config file: {e}")

    # Validate required fields
    if "mastodon_server_url" not in data:
        raise ConfigError("Missing required field 'mastodon_server_url' in config")

    # Build config with all available fields
    config = Config(mastodon_server_url=str(data["mastodon_server_url"]))

    if "mastodon_access_token" in data:
        config["mastodon_access_token"] = str(data["mastodon_access_token"])
    if "client_id" in data:
        config["client_id"] = str(data["client_id"])
    if "client_secret" in data:
        config["client_secret"] = str(data["client_secret"])

    return config


def write_config(config: Config) -> None:
    """Write configuration to file.

    Args:
        config: Configuration dictionary to write

    Raises:
        ConfigError: If unable to write config file
    """
    ensure_config_dir()
    config_path = get_config_path()

    try:
        with open(config_path, "wb") as f:
            tomli_w.dump(dict(config), f)
    except Exception as e:
        raise ConfigError(f"Failed to write config file: {e}")


def validate_config(config: Config, require_access_token: bool = True) -> bool:
    """Validate configuration values.

    Args:
        config: Configuration to validate
        require_access_token: Whether to require access_token (False during OAuth setup)

    Returns:
        True if valid

    Raises:
        ConfigError: If validation fails
    """
    if not config.get("mastodon_server_url"):
        raise ConfigError("mastodon_server_url cannot be empty")

    # Basic URL validation
    if not config["mastodon_server_url"].startswith(("http://", "https://")):
        raise ConfigError("mastodon_server_url must start with http:// or https://")

    # Check for access token if required
    if require_access_token and not config.get("mastodon_access_token"):
        raise ConfigError("mastodon_access_token cannot be empty")

    return True


def create_sample_config() -> None:
    """Create a sample configuration file with placeholder values.

    Raises:
        ConfigError: If config already exists or unable to create
    """
    if config_exists():
        raise ConfigError("Configuration file already exists")

    sample_config = Config(
        mastodon_server_url="https://mastodon.social",
        mastodon_access_token="your-access-token-here",
    )

    write_config(sample_config)
