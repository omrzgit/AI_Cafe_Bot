import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CalendarNotConfiguredError(Exception):
    """Raised when Google Calendar credentials are missing or incomplete."""
    pass

class CalendarService:
    def __init__(self):
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service

        if not all([
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_refresh_token,
        ]):
            raise CalendarNotConfiguredError(
                "Google Calendar credentials not configured. "
                "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in .env"
            )

        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = Credentials(
            token=None,
            refresh_token=settings.google_refresh_token,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/calendar"],
        )

        request = Request()
        creds.refresh(request)

        self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    async def create_event(
        self,
        summary: str,
        description: str,
        start_datetime: datetime,
        duration_minutes: int,
        attendee_email: str,
        timezone: str = "Asia/Kolkata",
    ) -> dict:
        """
        Create a Google Calendar event and return a dict containing:
          - id: the Calendar event ID
          - meet_link: Google Meet URL (if conference data was created)
          - html_link: link to the event in Google Calendar
        """
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._create_event_sync, {
            "summary": summary,
            "description": description,
            "start_datetime": start_datetime,
            "duration_minutes": duration_minutes,
            "attendee_email": attendee_email,
            "timezone": timezone,
        })
        return result

    def _create_event_sync(self, params: dict) -> dict:
        service = self._get_service()

        start_dt: datetime = params["start_datetime"]
        end_dt = start_dt + timedelta(minutes=params["duration_minutes"])

        event_body = {
            "summary": params["summary"],
            "description": params["description"],
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": params["timezone"],
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": params["timezone"],
            },
            "attendees": [{"email": params["attendee_email"]}],
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        created = (
            service.events()
            .insert(
                calendarId=settings.google_calendar_id,
                body=event_body,
                conferenceDataVersion=1,
                sendUpdates="all",
            )
            .execute()
        )

        meet_link = None
        conference_data = created.get("conferenceData", {})
        for entry_point in conference_data.get("entryPoints", []):
            if entry_point.get("entryPointType") == "video":
                meet_link = entry_point.get("uri")
                break

        return {
            "id": created["id"],
            "meet_link": meet_link,
            "html_link": created.get("htmlLink"),
        }

    async def delete_event(self, event_id: str) -> None:
        """Delete a calendar event by its ID."""
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._delete_event_sync, event_id)

    def _delete_event_sync(self, event_id: str) -> None:
        service = self._get_service()
        service.events().delete(
            calendarId=settings.google_calendar_id,
            eventId=event_id,
            sendUpdates="all",
        ).execute()

    async def get_event(self, event_id: str) -> Optional[dict]:
        """Retrieve a calendar event by its ID."""
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_event_sync, event_id)

    def _get_event_sync(self, event_id: str) -> Optional[dict]:
        try:
            service = self._get_service()
            return service.events().get(
                calendarId=settings.google_calendar_id,
                eventId=event_id,
            ).execute()
        except Exception as e:
            logger.warning(f"Failed to get calendar event {event_id}: {e}")
            return None
