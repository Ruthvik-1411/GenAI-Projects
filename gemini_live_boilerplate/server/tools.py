"""Common module for function tools"""
# pylint: disable=line-too-long
from enum import Enum
from typing import Optional, Annotated
from utils import function_tool # pylint: disable=no-name-in-module

class MeetingRoom(Enum):
    """Enum class for meeting room"""
    VIRTUAL = "virtual"
    TINKERSTATION = "tinker_station"
    MINDMANOR = "mind_manor"

# @function_tool
# def schedule_meet(attendees: list[str],  topic: str, date: str, time_slot: str = "Now"):
#     """Schedules meeting for a given list of attendees at a given time and date"""
#     response_message = f"Meeting with Topic: '{topic}' is successfully scheduled. \n\n"
#     response_message += f"Meeting Details: \n Attendeed: {attendees}. \n Date: {date} \n Time slot: {time_slot}"

#     return response_message

# response = schedule_meet(attendees=["a","b","c"], topic="ML", date="01/01/2025")
# print(response)
# print(json.dumps(schedule_meet.tool_metadata(), indent=2))

@function_tool
def schedule_meet_tool(
    attendees: Annotated[list[str], "List of the people attending the meeting"],
    topic: Annotated[str, "The subject or the topic of the meeting"],
    date: Annotated[str, "The date of the meeting (e.g., 25/06/2025)"],
    meeting_room: Annotated[MeetingRoom, "The name of the meeting room."] = MeetingRoom.VIRTUAL,
    time_slot: Annotated[Optional[str], "Time of the meeting (e.g., '14:00'-'15:00'). Immediate schedule if value not provided."] = "Now"):
    """Schedules meeting for a given list of attendees at a given time and date"""

    response_message = f"Meeting with Topic: '{topic}' is successfully scheduled. \n\n"
    response_message += f"**Meeting Details**:\nAttendees: {attendees}.\nMeeting room: {meeting_room.value}\nDate: {date}\nTime slot: {time_slot}"

    return response_message

@function_tool
def cancel_meet_tool(meet_id: Annotated[str, "The id of the meeting to cancel in lower case"]):
    """Cancels the meeting with the given ID"""

    if meet_id.startswith("a"):
        response_message = f"Successfully cancelled meeting with ID: {meet_id}"
        return response_message
    if meet_id.startswith("b"):
        response_message = "The meeting is currently in progress, unable to cancel this meeting."
        return response_message

    return "An error occurred while cancelling the meeting. Please make sure meeting ID is valid."
