# peTTY

peTTY is a TUI-based follower tracker for Mastodon now, other federated services
services maybe someday. It's also a project for me to learn [Textual], so it may
not actually be good code. But it seems to work for me.

[Textual]: https://textual.textualize.io

## Getting started

For now, peTTY works best if you've got [uv] installed. Pull down this
repository and run

```shell
uv run petty
```

Let `uv` do its thing, oAuth into your Mastodon instance, and you're good to go.

[uv]: https://docs.astral.sh/uv/

## Usage

peTTY creates **snapshots** of follower data to track changes over time. Create your
first snapshot by selecting **Create Snapshot**.

Hit up **View Snapshots** to select and view a snapshot. Tab and arrow around to see
lists of who you're not following, who's not following you, and changes since the
previous snapshot. the UI is a little fiddly at the moment.

## Implementation details

peTTY's configuration and data are currently stored in `~/.config/petty`. Snapshot
data are in a SQLite database in that directory.

## Non-committal roadmap

- Better storage of oAuth secrets
- Multiple Mastodon account support
- BlueSky support
- Maybe support for other providers?
- Many, many UI tweaks
- Follow/unfollow within the app?
- More convenient packaging and distribution
