
from sources.general import BOT_PREFIX, Cmd

_TZ_GUIDE = "A valid time zone is something like `America/Chicago`. It's advised not to use abbreviations like EST, since those don't account for daylight savings time and one abbreviation can represent multiple time zones. For a list of valid timezones, check the entries of the \"TZ database name\" column on this Wikipedia page: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>."

class COG:
    NAME = "Task Cog"
    DESC = "A cog that will schedule and send you reminders."

class PATH:
    TZPREFS = "./sources/tzprefs.json"

class INFO:
    ALERT = lambda msg: f"Task time reached:\n{msg}"
    EVENT_CREATED = lambda eventTime, message: f"Event successfully added. ```Date: {eventTime}\nMessage: {message}```"
    TZ_USE_THIS = "Use this command to set your time zone. " + _TZ_GUIDE
    TZ_USING = lambda zone: f"You are currently using `{zone}` time."
    TZ_SUCCESS = lambda zone: f"Successfully set your timezone to `{zone}`."
    NOW = lambda zone, time: f"`{zone}` time is currently {time}."

class ERR:
    INVALID_SUBCOMMAND = lambda invalid: f"The entry (`{invalid}`) was not a valid subcommand."
    NO_ENTRY = "No entry was given to this command."
    NO_TZ = "You haven't set a timezone preference with `bel.timezone` yet."
    INVALID_TZ = lambda tz: f"{tz} is not a valid time zone. " + _TZ_GUIDE

CREATE = Cmd(
    "create", "make", "add", "new",
    f"A parent command to create tasks. Use `{BOT_PREFIX}help create` for more information.",
)
EVENT = Cmd(
    "task",
    f"""
        Creates a one-time event at some point in the future.
        The entry must have `in`, `on`, or `at` as the first word. Tasks created with `in` get created at a time relative to the current time. Tasks created with `on` or `at` get created with a specific time.
        After the first word, the time for the event is defined. This can be a number and a unit abbreviation (i.e. `1h 30m`, `1yr 6mo`), or a semicolon-formatted time (i.e. `1:20pm`, `13:20`). When creating a specifically-timed event, any unit not specified will be filled in with the current date's unit (i.e. when doing `create event at 7:00pm 20th` and the date is the 2nd of March, 2024, the month and year will be set to March and 2024 respectively even though they aren't specified).
        After the time is defined, the rest of the entry is treated as the message that will be displayed when the event fires.
    """,
    usage=[
        "in 1h change laundry",
        "at 9:25pm writing sprint",
        "on 25th Oct 2022 9:00am Jess' birthday"
    ]
)
TASKS = Cmd(
    "tasks", "list",
    f"""
        Get a numbered list of your currently scheduled tasks.
    """
)
TIMEZONE = Cmd(
    "timezone", "tz",
    f"""
        If used on its own, gets the time zone you're currently using. Otherwise, sets your current time zone.
        {_TZ_GUIDE}
    """,
    usage=[
        "US/Eastern",
        "us/central",
        "america/detroit"
    ]
)
NOW = Cmd(
    "now",
    f"""
        Gets the current time based on your time zone.
    """
)