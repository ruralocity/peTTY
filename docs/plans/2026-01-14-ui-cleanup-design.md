# UI Cleanup Design

Clean up the peTTY TUI for consistency across screens and improved intuitiveness.

## Navigation Model

### Escape Behavior
- On any screen except MainMenuScreen: go back to previous screen
- On MainMenuScreen: do nothing (it's the root)

### Quit Behavior
- `q` quits from any screen
- Footer shows `q Quit` on every screen

### Footer Bindings by Screen

| Screen | Footer |
|--------|--------|
| MainMenuScreen | `c Create Snapshot · v View Snapshots · q Quit` |
| CreateSnapshotScreen | `Esc Back · q Quit` |
| ViewSnapshotsScreen | `Esc Back · Enter View · d Delete · q Quit` |
| SnapshotDetailScreen | `Esc Back · 1-4 Switch Tabs · q Quit` |
| OAuthSetupScreen | `Esc Quit` (no back destination during setup) |

### Back Buttons
All back buttons display "Back" (not "Back to Menu" or "Back to List").

## Information Density

### SnapshotDetailScreen Account Lists

Replace the current 3-line card format with a compact table:

```
Not Following Back (12 accounts)
────────────────────────────────────────────────────
@username            Display Name
@another_user        Another Person
@someone_else        Someone With A Longer Name
```

- Header shows list type and count
- Two-column table: username (left), display name (right)
- URL dropped (not clickable in TUI)
- No borders or backgrounds per row
- Separator line under header

## Visual Consistency

### Container Width
All screens use 90% width (adapts to terminal size).

### Title Styling
- Centered, accent color
- 1 line margin below
- Consistent class usage across all screens

### Button Styling
- Action buttons (Create Snapshot, View Details): `variant="primary"`
- Destructive buttons (Delete): `variant="error"`
- Navigation buttons (Back): `variant="default"`
- Buttons centered in horizontal row, not full-width

### Spacing
- Container padding: 1 unit vertical, 2 units horizontal
- Section margin: 1 unit between major sections

### Borders
All main containers use `border: thick $primary`.
