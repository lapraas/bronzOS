
from sources.general import BOT_PREFIX as bel, Cmd

_TZ_GUIDE = "A valid time zone is something like `America/Chicago`. It's advised not to use abbreviations like EST, since those don't account for daylight savings time and one abbreviation can represent multiple time zones. For a list of valid timezones, check the entries of the \"TZ database name\" column on this Wikipedia page: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>."

CREATE = Cmd(
    "create", "make", "add", "new", "task", "event",
    f"""
        Creates a new task with a given time.
        This time can be relative to when the command was issued, a specific time, or a repeating time.

        To make a relatively-timed task, the entry must start with the word `in`.
        To make a specifically-timed task, the entry must start with either `on` or `at`.
        To make a repeated task, the entry must start with any of `yearly`, `monthly`, `weekly`, `daily`, `hourly`, `every year`, `every month`, `every week`, `every day`, or `every hour`.

        Time is specified with amount-unit abbreviation pairs, such as `30m` for 30 minutes, `1h` for 1 hour, etc.
        ```
        yr   | year
        mo   | month
        w    | week
        d    | day
        h    | hour
        m    | minute
        s    | second
        ```
        Semicolon-formatted time, such as 1:20pm or 13:20, also works.
        Specific days are recognized if they are spelled out fully (`monday`) or abbreviated (`mon`).
        Specific months are recognized if they are spelled out fully (`february`) or abbreviated (`feb`).
        Four-digit numbers (`2021`) are interpreted as years.

        Not all units of time have to be specified for a specifically-timed task. Any units that are omitted are taken from the current date, or if the task would be set in the past, the next valid date. This means that `create at 2:00pm` would create an event on the current date at 2:00 in the afternoon if it's before that time, or 2:00 in the afternoon tomorrow otherwise. As another example, `create at :00` will always create an event at the top of the upcoming hour.

        Repeated task parsing behaves similarly to specifically-timed task parsing, but instead of creating a one-off task, it will reschedule itself for some time in the future based on the frequency specified.

        Any word that isn't matched as a time definition marks the start of the message the task will display when its time is reached.
    """,
    usage=[
        "in 1h change laundry",
        "at 9:25pm writing sprint",
        "on 25th Oct 2022 9:00am Jess' 19th birthday",
        "every week mon 8:00am class",
        "yearly Dec 25th Christmas"
    ]
)
TASKS = Cmd(
    "tasks", "list", "ls",
    f"""
        Get a numbered list of your currently scheduled tasks.
    """
)
REMOVE = Cmd(
    "remove", "delete", "rm", "del"
    f"""
        Remove a task from your list of scheduled tasks.
    """,
    usage=[
        "1",
        "2"
    ]
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

class COG:
    NAME = "Task Cog"
    DESC = "A cog that will schedule and send you reminders."

class PATH:
    TZPREFS = "./sources/tzprefs.json"
    TASKMASTER = "./sources/taskmaster.json"

class INFO:
    ALERT = lambda msg: f"Task time reached:\n{msg}"
    TASK_CREATED = lambda eventTime, message: f"Task successfully added. ```Date: {eventTime}\nMessage: {message}```"
    TZ_USE_THIS = "Use this command to set your time zone. " + _TZ_GUIDE
    TZ_USING = lambda zone: f"You are currently using `{zone}` time."
    TZ_SUCCESS = lambda zone: f"Successfully set your timezone to `{zone}`."
    NOW = lambda zone, time: f"`{zone}` time is currently {time}."
    TASKS_HEADER = f"Your currently-scheduled tasks:"
    TASKS = lambda num, spacing, eventText, message: f"\n\n{spacing}{num} | {eventText}\n{spacing}{' '*len(num)} | {message}"
    REMOVE_SUCCESS = lambda i, message: f"Successfully removed task `{i}` (`{message}`)"

class ERR:
    NO_ENTRY = f"No entry was given to this command. For help, use `{bel}help {CREATE.name}`."
    NO_TZ = f"You haven't set a timezone preference with {TIMEZONE.refF} yet. For help, use `{bel}help {TIMEZONE.name}`."
    INVALID_TZ = lambda tz: f"{tz} is not a valid time zone. For help, use `{bel}help {TIMEZONE.name}`."
    NO_TASKS = f"You have no tasks. To create a task, use {CREATE.refF}. Make sure you've set your time zone preference with {TIMEZONE.refF} beforehand."
    REMOVE_OOB = lambda i, leng: f"The index specified, `{i}`, is invalid. You only have `{leng}` task{'s' if leng > 1 else ''}."