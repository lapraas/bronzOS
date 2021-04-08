
import datetime as dt
import inspect
import re
from types import CoroutineType
import pytz
from typing import Callable, Literal, Optional

class TaskException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

def isInt(string):
    return all(c in "1234567890" for c in string)

WEEKDAYS = [
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun"
]
MONTHS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec"
]

timePartPat = re.compile(r"([\d|:]+)([a-zA-Z]+)")

class Parser:
    def __init__(self, args: list[str]):
        self.ref: Optional[Literal["in", "on", "at"]] = None
        self.message: Optional[str] = None
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.day: Optional[int] = None
        self.hour: Optional[int] = None
        self.minute: Optional[int] = None
        self.second: Optional[int] = None

        self.i: int = 0

        self.parse(args)

    def parse(self, args: list[str]):
        entry = ' '.join(args)
        self.ref, *args = args
        if not self.ref in ["in", "on", "at"]:
            raise TaskException(f"The entry `{entry}` had an invalid reference point `{self.ref}`. Must be one of `in`, `on`, or `at`.")

        timeparts: list[re.Match] = []
        for i, arg in enumerate(args):
            timePartMatch = timePartPat.search(arg)
            if timePartMatch:
                part = (timePartMatch.group(1), timePartMatch.group(2))

                timeparts.append(part)
                continue
            break
        if not timeparts:
            raise TaskException(f"The entry `{entry}` did not specify a time.")
        self.message = " ".join(args[i:])

        num: str
        unit: str
        for num, unit in timeparts:
            if unit == "yr":
                self.year = int(num)
            elif unit == "mo":
                self.month = int(num)
            elif unit == "w":
                self.day = int(num) * 7
            elif unit == "d":
                self.day = int(num)
            elif unit == "h":
                self.hour = int(num)
            elif unit in ["am", "pm"] or ":" in num:
                if ":" in num:
                    h, m = num.split(":", 1)
                    self.hour = int(h) + (0 if unit == "am" else 12)
                    self.minute = int(m)
                else:
                    self.hour = int(num) + (0 if unit == "am" else 12)
            elif unit == "m":
                self.minute = int(num)
            elif unit == "s":
                self.second = int(num)
            else:
                raise TaskException(f"The time part `{str(num) + unit}` in the entry `{entry}` had an invalid unit. Must be one of `w`, `d`, `h`, `m`, or `s`.")
    
    def getTimeFromToday(self, today: dt.datetime):
        if self.ref in ["at", "on"]:
            if self.year == None: self.year = today.year
            if self.month == None: self.month = today.month
            if self.day == None: self.day = today.day
            if self.hour == None: self.hour = today.hour
            if self.minute == None: self.minute = today.minute
            if self.second == None: self.second = today.second
        else:
            self.year = today.year if self.year == None else self.year + today.year
            self.month = today.month if self.month == None else self.month + today.month
            self.day = today.day if self.day == None else self.day + today.day
            self.hour = today.hour if self.hour == None else self.hour + today.hour
            self.minute = today.minute if self.minute == None else self.minute + today.minute
            self.second = today.second if self.second == None else self.second + today.second
        return dt.datetime(self.year, self.month, self.day, self.hour, self.minute, self.second, tzinfo=today.tzinfo)
    
    def getMessage(self):
        return self.message


class Event:
    def __init__(self, when: dt.datetime, callback: Callable[[], None], args: list=[], kwargs: dict={}):
        # What the Task will do when it fires.
        self.callback = callback
        # What to give the callback when the Task fires.
        self.callbackArgs = args
        self.callbackKwargs = kwargs
        # When the Task will fire.
        self.when = when
        # A flag to set when the Task is done.
        self.kill = False
    
    async def tick(self, time: dt.datetime):
        if time >= self.when:
            self.kill = True
            await self.fire()
    
    async def fire(self):
        res = self.callback(*self.callbackArgs, **self.callbackKwargs)
        if inspect.isawaitable(res):
            await res

class Recur(Event):
    def __init__(self, when: dt.datetime, interval: dt.timedelta, callback: Callable[[], None], args: list=[], kwargs: dict={}):
        super().__init__(when, callback, args, kwargs)
        self.interval = interval
    
    async def tick(self, time: dt.datetime):
        if time >= self.when:
            await self.fire()
            self.when = self.when + self.interval

    def cancel(self):
        self.kill = True

class Taskmaster:
    def __init__(self):
        self.tasks: list[Event] = []
    
    async def update(self, time: dt.datetime):
        index = 0
        while index < len(self.tasks):
            task = self.tasks[index]
            await task.tick(time)
            if task.kill:
                index -= 1
                self.tasks.remove(task)
            index += 1
    
    def addTask(self, task: Event):
        self.tasks.append(task)
        