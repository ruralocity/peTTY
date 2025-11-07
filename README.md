# peTTY

A TUI-based follow/unfollow tracker.

## Configuration

peTTY requires a configuration file to connect to your Mastodon account.

### Config File Location

`~/.config/petty/config.toml`

### Setup

1. Create the configuration directory:
   ```bash
   mkdir -p ~/.config/petty
   ```

2. Create `~/.config/petty/config.toml` with the following content:
   ```toml
   mastodon_server_url = "https://your-mastodon-instance.com"
   mastodon_access_token = "your-access-token-here"
   ```

### Getting Your Mastodon Access Token

1. Log in to your Mastodon account
2. Go to **Settings** → **Development** → **New Application**
3. Give your application a name (e.g., "peTTY")
4. Required scopes: `read:accounts`, `read:follows`
5. Click **Submit**
6. Copy the **Access Token** from the application details page
7. Paste it into your config file as `mastodon_access_token`

### Example Configuration

```toml
mastodon_server_url = "https://mastodon.social"
mastodon_access_token = "abc123def456..."
```
