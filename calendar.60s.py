#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "google-api-python-client",
#     "google-auth-httplib2",
#     "google-auth-oauthlib",
#     "swiftbarmenu",
# ]
# ///
# <xbar.title>Google Calendar Events</xbar.title>
# <xbar.version>v2.0</xbar.version>
# <xbar.author>Sam Clark</xbar.author>
# <xbar.author.github>samclark2015</xbar.author.github>
# <xbar.desc>Displays today and tomorrow's Google Calendar events with meeting links</xbar.desc>
# <xbar.dependencies>uv</xbar.dependencies>
# <xbar.abouturl>https://github.com/samclark2015/swiftbar-calendar</xbar.abouturl>

import datetime
import os
import os.path
import pickle
import re
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from swiftbarmenu.menu import Menu

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, ".data")
TOKEN_PATH = os.path.join(DATA_DIR, "token.pickle")
CREDENTIALS_PATH = os.path.join(DATA_DIR, "credentials.json")


def get_credentials():
    """Get valid user credentials, or None if not available."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Check if credentials exist and are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(TOKEN_PATH, "wb") as token:
                    pickle.dump(creds, token)
            except Exception:
                return None
        else:
            return None

    return creds


def login():
    """Run the OAuth login flow."""
    if not os.path.exists(CREDENTIALS_PATH):
        menu = Menu("🔑 Error")
        menu.add_item("credentials.json not found")
        menu.add_item("Place credentials.json in calendar/.data/")
        menu.dump()
        sys.exit(1)

    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
        print("Login successful! Refresh SwiftBar to see events.")
    except Exception as e:
        print(f"Login failed: {e}")
        sys.exit(1)


def parse_datetime(dt_string):
    """Parse ISO datetime string to datetime object."""
    if "T" in dt_string:
        # Has time component
        if dt_string.endswith("Z"):
            return datetime.datetime.fromisoformat(dt_string[:-1] + "+00:00")
        return datetime.datetime.fromisoformat(dt_string)
    else:
        # All-day event
        return datetime.datetime.fromisoformat(dt_string + "T00:00:00")


def pluralize(count, singular, plural=None):
    """Return singular or plural form based on count."""
    if plural is None:
        plural = singular + "s"
    return singular if count == 1 else plural


def format_time(dt):
    """Format datetime for display."""
    return dt.strftime("%-I:%M %p")


def get_time_until(start_dt, now):
    """Get human-readable time until event starts."""
    delta = start_dt - now
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        # Event already started
        return "Now"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0:
        return f"In {hours} {pluralize(hours, 'hour')}"
    elif minutes > 0:
        return f"In {minutes} {pluralize(minutes, 'minute')}"
    else:
        return "Now"


def get_duration(start_dt, end_dt):
    """Calculate duration between two datetimes."""
    delta = end_dt - start_dt
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{minutes}m"


def get_conference_link(event):
    """Extract video conference link from event."""
    # Check for hangoutLink (Google Meet)
    if "hangoutLink" in event:
        return event["hangoutLink"]

    # Check for conferenceData
    if "conferenceData" in event and "entryPoints" in event["conferenceData"]:
        for entry in event["conferenceData"]["entryPoints"]:
            if entry.get("entryPointType") == "video":
                return entry.get("uri")

    # Check event description or location for common conference links
    for field in ["description", "location"]:
        if field in event:
            text = event[field]
            # Common patterns for video conference links
            patterns = [
                "zoom.us",
                "meet.google.com",
                "teams.microsoft.com",
                "webex.com",
            ]
            for pattern in patterns:
                if pattern in text.lower():
                    # Extract URL
                    match = re.search(
                        r'https?://[^\s<>"]+' + pattern + r'[^\s<>"]*',
                        text,
                        re.IGNORECASE,
                    )
                    if match:
                        return match.group(0)

    return None


def get_attendee_count(event):
    """Get number of attendees (excluding self)."""
    if "attendees" not in event:
        return 0

    # Filter out the organizer/self
    attendees = [a for a in event["attendees"] if not a.get("self", False)]
    return len(attendees)


def add_event_to_menu(menu, event, now):
    """Add a calendar event to the menu."""
    start_str = event["start"].get("dateTime", event["start"].get("date"))
    end_str = event["end"].get("dateTime", event["end"].get("date"))

    start_dt = parse_datetime(start_str)
    end_dt = parse_datetime(end_str)

    # Make timezone aware if naive
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)

    # Convert to local time for display
    start_local = start_dt.astimezone()
    end_local = end_dt.astimezone()

    summary = event.get("summary", "Untitled Event")
    duration = get_duration(start_local, end_local)
    attendee_count = get_attendee_count(event)
    conference_link = get_conference_link(event)

    # Check if event is happening now
    is_now = start_dt <= now <= end_dt
    status_emoji = "🔴 " if is_now else ""

    # Format the main line
    time_range = f"{format_time(start_local)} - {format_time(end_local)}"
    attendees_text = ""
    if attendee_count > 0:
        attendees_text = f" • {attendee_count} {pluralize(attendee_count, 'attendee')}"

    event_line = f"{status_emoji}{time_range} ({duration}) • {summary}{attendees_text}"

    # Add menu item with link if available
    if conference_link:
        menu.add_item(event_line, href=conference_link)
    else:
        menu.add_item(event_line)


def main() -> None:
    """Display calendar events in SwiftBar format."""
    # Check if login action was requested
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        login()
        return

    # Try to get credentials
    creds = get_credentials()

    if not creds:
        # Not logged in or token expired
        menu = Menu("🔑❌")
        menu.add_action(
            "Login to Google Calendar", ["login"], terminal=True, refresh=True
        )
        menu.dump()
        return

    try:
        service = build("calendar", "v3", credentials=creds)

        # Get timezone-aware now
        now = datetime.datetime.now(datetime.timezone.utc)

        # Get start of today and end of tomorrow in local time
        local_now = datetime.datetime.now()
        today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = (today_start + datetime.timedelta(days=2)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Convert to UTC for API
        time_min = today_start.astimezone(datetime.timezone.utc).isoformat()
        time_max = tomorrow_end.astimezone(datetime.timezone.utc).isoformat()

        # Call the Calendar API
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        # Filter events for today that haven't ended yet
        today_events = []
        tomorrow_events = []
        remaining_today = 0

        for event in events:
            start_str = event["start"].get("dateTime", event["start"].get("date"))
            end_str = event["end"].get("dateTime", event["end"].get("date"))

            start_dt = parse_datetime(start_str)
            end_dt = parse_datetime(end_str)

            # Make timezone aware if naive
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)

            # Check if event is today or tomorrow
            event_date = start_dt.astimezone().date()
            today_date = local_now.date()
            tomorrow_date = (local_now + datetime.timedelta(days=1)).date()

            if event_date == today_date:
                today_events.append(event)
                # Count if event hasn't ended yet and has other attendees
                if end_dt > now and get_attendee_count(event) > 0:
                    remaining_today += 1
            elif event_date == tomorrow_date:
                tomorrow_events.append(event)

        # Build menu with header
        if remaining_today > 0:
            # Find next meeting
            next_meeting = None
            for event in today_events:
                start_str = event["start"].get("dateTime", event["start"].get("date"))
                end_str = event["end"].get("dateTime", event["end"].get("date"))
                start_dt = parse_datetime(start_str)
                end_dt = parse_datetime(end_str)

                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)

                if end_dt > now:
                    next_meeting = event
                    break

            if next_meeting:
                # Get countdown to next meeting
                start_str = next_meeting["start"].get(
                    "dateTime", next_meeting["start"].get("date")
                )
                start_dt = parse_datetime(start_str)
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=datetime.timezone.utc)

                countdown = get_time_until(start_dt, now)
                # Subtract 1 from remaining_today to exclude the next/current meeting from "more" count
                more_count = remaining_today - 1
                if more_count > 0:
                    menu = Menu(f"📅 {countdown} - {more_count} more")
                else:
                    menu = Menu(f"📅 {countdown}")
            else:
                menu = Menu(f"📅 {remaining_today}")
        else:
            menu = Menu("😴 No more meetings")

        # Display today's events
        menu.add_item("Today")
        if today_events:
            for event in today_events:
                add_event_to_menu(menu, event, now)
        else:
            menu.add_item("No events today")

        menu.add_sep()

        # Display tomorrow's events
        menu.add_item("Tomorrow")
        if tomorrow_events:
            for event in tomorrow_events:
                add_event_to_menu(menu, event, now)
        else:
            menu.add_item("No events tomorrow")

        # Add refresh option
        menu.add_action_refresh()

        # Render the menu
        menu.dump()

    except Exception as e:
        menu = Menu("📅 ⚠️")
        menu.add_item(f"Error: {str(e)}")
        menu.add_action("Re-login", ["login"], terminal=True, refresh=True)
        menu.dump()


if __name__ == "__main__":
    main()
