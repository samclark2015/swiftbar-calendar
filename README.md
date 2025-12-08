# SwiftBar Calendar Plugin

A SwiftBar plugin that displays your Google Calendar events directly in the macOS menu bar.

## Features

- 📅 Shows countdown to next meeting in menu bar
- 🔴 Highlights currently active meetings
- 📊 Displays today's and tomorrow's events
- 👥 Shows attendee count for each event
- 🔗 Click to join video conferences (Google Meet, Zoom, Teams, Webex)
- ⏱️ Shows event duration and time ranges
- 🔄 Auto-refreshes every 60 seconds
- 😴 Only counts meetings with other attendees

## Menu Bar Display

The menu bar shows:
- **Countdown format**: "In 45m - 3 more" (time until next meeting, number of meetings remaining today)
- **No meetings**: "😴 No more meetings"

## Requirements

- macOS Catalina (10.15) or later
- [SwiftBar](https://swiftbar.app/) installed
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Google Calendar API credentials

## Installation

1. Install SwiftBar:
   ```bash
   brew install swiftbar
   ```

2. Install uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Clone or download this repository

4. Set up Google Calendar API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials as `credentials.json`

5. Place `credentials.json` in the `calendar/.data/` directory

6. Move the `calendar` folder to your SwiftBar plugin directory

7. The plugin will automatically execute using `uv` to manage dependencies

## First Run

On first run, the plugin will:
1. Show "🔑❌" in the menu bar
2. Offer a "Login to Google Calendar" option
3. Open your browser for Google OAuth authentication
4. Save your authentication token for future use

## File Structure

```
calendar/
├── calendar.60s.py      # Main plugin script
├── .data/               # Stores credentials and token
│   ├── credentials.json # Your Google API credentials
│   └── token.pickle     # OAuth token (auto-generated)
└── README.md           # This file
```

## Configuration

- **Refresh interval**: Change the filename to adjust (e.g., `calendar.30s.py` for 30 seconds)
- **Credentials location**: Stored in `calendar/data/` directory
- **Python version**: Requires Python 3.13+ (specified in script header)

## Dependencies

Dependencies are managed automatically by `uv` from the script header:
- `google-api-python-client` - Google Calendar API client
- `google-auth-httplib2` - HTTP library for Google authentication
- `google-auth-oauthlib` - OAuth 2.0 authentication
- `swiftbarmenu` - SwiftBar menu building library

## Troubleshooting

### "🔑❌" appears in menu bar
- Click the menu and select "Login to Google Calendar"
- Complete the OAuth flow in your browser

### "📅 ⚠️" appears in menu bar
- Click the menu to see the error details
- Try re-logging in if authentication failed
- Check that `credentials.json` is in the `data/` directory

### No events showing
- Ensure you have events in your primary Google Calendar
- Check that events are scheduled for today or tomorrow
- Solo calendar items (no attendees) don't count toward the meeting counter

### Plugin not appearing
- Check that SwiftBar is running
- Verify the file is executable: `chmod +x calendar.60s.py`
- Ensure `uv` is installed and in your PATH
- Check SwiftBar logs for errors

## Privacy & Security

- OAuth tokens are stored locally in `data/token.pickle`
- Only read access to your calendar is requested
- No data is sent to external services (except Google Calendar API)
- Credentials are stored locally and never shared

## License

This plugin is provided as-is for personal use.

## Credits

Built using:
- [SwiftBar](https://swiftbar.app/) by [@melonamin](https://github.com/melonamin)
- [swiftbarmenu](https://pypi.org/project/swiftbarmenu/) by [@sdelquin](https://github.com/sdelquin)
- [Google Calendar API](https://developers.google.com/calendar)
- [uv](https://docs.astral.sh/uv/) by Astral
