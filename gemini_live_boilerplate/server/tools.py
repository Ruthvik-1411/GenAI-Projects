"""Common module for function tools"""
# pylint: disable=line-too-long
from enum import Enum
from typing import Optional, Annotated
import uuid
import datetime
from utils import function_tool # pylint: disable=no-name-in-module
from tool_context import ToolContext # pylint: disable=no-name-in-module

class MeetingRoom(Enum):
    """Enum class for meeting room"""
    VIRTUAL = "virtual"
    TINKERSTATION = "tinker_station"
    MINDMANOR = "mind_manor"

@function_tool
def schedule_meet_tool(
    tool_ctx: ToolContext,
    attendees: Annotated[list[str], "List of the people attending the meeting"],
    topic: Annotated[str, "The subject or the topic of the meeting"],
    date: Annotated[str, "The date of the meeting (e.g., 25/06/2025)"],
    meeting_room: Annotated[MeetingRoom, "The name of the meeting room."] = MeetingRoom.VIRTUAL,
    time_slot: Annotated[Optional[str], "Time of the meeting (e.g., '14:00'-'15:00'). Immediate schedule if value not provided."] = "Now",
    ):
    """Schedules meeting for a given list of attendees at a given time and date"""
    meet_id = str(uuid.uuid4())[:5]

    if tool_ctx:
        meeting_details = {
            "meet_id": meet_id,
            "attendees": attendees,
            "topic": topic,
            "date": date,
            "meeting_room": meeting_room,
            "time_slot": time_slot
        }
        # Update the state with these new values
        # There are a lot of ways to customize this
        tool_ctx.update(**meeting_details)
        print(f"Current State: {tool_ctx.dump_state()}")

    response_message = f"Meeting with Topic: '{topic}' is successfully scheduled with ID {meet_id}. \n\n"
    response_message += f"**Meeting Details**:\nAttendees: {attendees}.\nMeeting room: {meeting_room}\nDate: {date}\nTime slot: {time_slot}"

    return response_message

@function_tool
def cancel_meet_tool(meet_id: Annotated[str, "The id of the meeting to cancel in lower case"],
                     tool_ctx: ToolContext):
    """Cancels the meeting with the given ID"""

    try:
        if tool_ctx.get("meet_id") == meet_id:
            # We can add more logic here, but keeping it simple for now
            print(f"Current State: {tool_ctx.dump_state()}")
            return f"Successfully cancelled meeting with ID: {meet_id}"
        else:
            return f"Meeting with ID: {meet_id} does not exist."
    except Exception as e:
        print(f"Error occured when canceling a meeting. {str(e)}")
        return "An error occurred while cancelling the meeting. Please make sure meeting ID is valid."

@function_tool
async def get_current_time(country: Annotated[str, "Name of the country"]) -> dict:
    """Returns the current time in a specified country."""
    if country.lower() == "india":
        tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {country}."
            ),
        }

    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {country} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "result": report}
