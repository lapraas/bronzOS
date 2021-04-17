
from __future__ import annotations
import calendar
import datetime as dt
from pytz import timezone
import re
from typing import Optional, Union

from sources.general import _FORMAT

class TaskException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

WEEKDAYS = [
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun"
]
WEEKDAYS_FULL = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
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
MONTHS_FULL = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december"
]

timePartPat = re.compile(r"([\d|:]+)([a-zA-Z]+)")
RECURRING = 1
SPECIFIC = 2
RELATIVE = 3

YEARLY = "yearly"
MONTHLY = "monthly"
WEEKLY = "weekly"
DAILY = "daily"
HOURLY = "hourly"

UTC = timezone("UTC")

class TaskTime:
    def __init__(self, original: Optional[TaskTime]=None):
        self.year: Optional[int] = original.year if original else None
        self.month: Optional[int] = original.month if original else None
        self.weekday: Optional[int] = original.weekday if original else None
        self.day: Optional[int] = original.day if original else None
        self.hour: Optional[int] = original.hour if original else None
        self.minute: Optional[int] = original.minute if original else None
        self.second: Optional[int] = original.second if original else None
    
    def hasData(self):
        return any([x != None for x in [
            self.year,
            self.month,
            self.weekday,
            self.day,
            self.hour,
            self.minute,
            self.second
        ]])
        
    def getDatetime(self, now: dt.datetime, ref: Union[SPECIFIC, RELATIVE]) -> dt.datetime:
        yr, mo, d, h, m, s = self.year, self.month, self.day, self.hour, self.minute, self.second
        
        if ref == SPECIFIC:
            if yr == None: yr = now.year
            if mo == None: mo = now.month
            if d == None: d = now.day
            if h == None: h = now.hour
            if m == None: m = now.minute
            if s == None: s = 0
        else:
            yr = now.year if yr == None else yr + now.year
            mo = now.month if mo == None else mo + now.month
            d = now.day if d == None else d + now.day
            h = now.hour if h == None else h + now.hour
            m = now.minute if m == None else m + now.minute
            s = now.second if s == None else s + now.second
                
        if self.weekday:
            toAdd = self.weekday - now.weekday()
            if toAdd < 0:
                toAdd += 7
            d += toAdd

        #wrap times
        daysInMonth = calendar.monthrange(now.year, now.month)[1]
        
        m2, s = divmod(s, 60)
        m += m2
        h2, m = divmod(m, 60)
        h += h2
        d2, h = divmod(h, 24)
        d += d2
        # datetime starts day and month at 1 rather than 0
        mo2, d = divmod(d - 1, daysInMonth)
        d += 1
        mo += mo2
        yr2, mo = divmod(mo - 1, 12)
        mo += 1
        yr += yr2

        datetime = dt.datetime(yr, mo, d, h, m, s, tzinfo=now.tzinfo)
        if datetime < now:
            if self.month != None and self.year == None:
                yr += 1
            elif self.weekday != None and self.month == None:
                d += 7
            elif self.day != None and self.month == None:
                mo += 1
            elif self.hour != None and self.day == None:
                d += 1
            elif self.minute != None and self.hour == None:
                h += 1
            elif self.second != None and self.minute == None:
                m += 1
            datetime = dt.datetime(yr, mo, d, h, m, s, tzinfo=now.tzinfo)
        return datetime

class Parser:
    def __init__(self, args: list[str]):
        self.ref: Optional[Union[RECURRING, SPECIFIC, RELATIVE]] = None
        self.message: Optional[str] = None
        self.recur: bool = False
        self.interval: Optional[str] = None
        self.time = TaskTime()

        self.i: int = 0

        self.parse(args)
    
    def processTimePart(self, num: Union[str, int], unit: str):

        if unit == "yr":
            self.time.year = int(num)
        elif unit == "mo":
            self.time.month = int(num)
        elif unit == "wkd":
            self.time.weekday = int(num)
        elif unit == "d":
            self.time.day = int(num)
        elif unit == "h":
            self.time.hour = int(num)
        elif unit in ["am", "pm"] or (isinstance(num, str) and ":" in num):
            if ":" in num:
                h, m = num.split(":", 1)
                if not m:
                    raise TaskException(f"Couldn't get a minute value from the time part `{num}`.")
                if h:
                    self.time.hour = int(h) + (12 if unit == "pm" else 0)
                self.time.minute = int(m)
            else:
                self.time.hour = int(num) + (12 if unit == "pm" else 0)
        elif unit == "m":
            self.time.minute = int(num)
        elif unit == "s":
            self.time.second = int(num)
        else:
            raise TaskException(f"The time part `{str(num) + unit}` had an invalid unit. Must be one of `yr`, `mo`, `w`, `d`, `h`, `m`, or `s`.")

    def parse(self, args: list[str]):
        entry = ' '.join(args)
        ref, *args = args
        ref = ref.lower()
        
        if ref in ["each", "every", "per"]:
            self.ref = RECURRING
        elif ref == "yearly":
            self.ref = RECURRING
            self.interval = YEARLY
        elif ref == "monthly":
            self.ref = RECURRING
            self.interval = MONTHLY
        elif ref == "weekly":
            self.ref = RECURRING
            self.interval = WEEKLY
        elif ref == "daily":
            self.ref = RECURRING
            self.interval = DAILY
        elif ref == "hourly":
            self.ref = RECURRING
            self.interval = HOURLY
        elif ref in ["on", "at"]:
            self.ref = SPECIFIC
        elif ref in ["in"]:
            self.ref = RELATIVE
        else:
            raise TaskException(f"The entry `{entry}` had an invalid reference point `{self.ref}`. Must be one of `in`, `on`, or `at`.")

        for i, arg in enumerate(args):
            timePartMatch = timePartPat.search(arg)
            lArg = arg.lower()
            if lArg == "year":
                self.interval = YEARLY
            elif lArg == "month":
                self.interval = MONTHLY
            elif lArg == "week":
                self.interval = WEEKLY
            elif lArg == "day":
                self.interval = DAILY
            elif lArg == "hour":
                self.interval = HOURLY
            elif any([lArg.endswith(x) for x in ["st", "nd", "th"]]):
                self.processTimePart(lArg[:-2], "d")
            elif lArg in MONTHS:
                self.processTimePart(MONTHS.index(lArg), "mo")
            elif lArg in MONTHS_FULL:
                self.processTimePart(MONTHS_FULL.index(lArg), "mo")
            elif lArg in WEEKDAYS:
                self.processTimePart(WEEKDAYS.index(lArg), "wkd")
            elif lArg in WEEKDAYS_FULL:
                self.processTimePart(WEEKDAYS_FULL.index(lArg), "wkd")
            elif all([n in "1234567890" for n in lArg]) and len(lArg) == 4:
                self.processTimePart(lArg, "yr")
            elif ":" in lArg:
                self.processTimePart(lArg, None)
            elif timePartMatch:
                self.processTimePart(timePartMatch.group(1), timePartMatch.group(2))
            else:
                break
        if not self.time.hasData():
            raise TaskException(f"The entry `{entry}` did not specify a time.")
        self.message = " ".join(args[i:])
    
    def getMessage(self):
        return self.message
    
    def getAsTask(self, now: dt.datetime) -> Task:
        if not self.ref == RECURRING:
            eventTime = self.time.getDatetime(now, self.ref)
            task = Task(eventTime.astimezone(UTC), self.message)
        else:
            eventTime = self.time.getDatetime(now, SPECIFIC) 
            task = Recur(eventTime.astimezone(UTC), self.message, self.interval)
        return task


class Task:
    def __init__(self, when: dt.datetime, message: str):
        # When the Task will fire.
        self.when = when
        # The message the Task will return when it fires.
        self.message = message
        # A flag to set when the Task is done.
        self.kill = False
    
    def asjson(self):
        obj = dict(
            when = self.when.isoformat(),
            message = self.message
        )
        return obj
    
    @staticmethod
    def fromjson(obj: dict[str, Union[str, int]]):
        when = dt.datetime.fromisoformat(obj["when"])
        message = obj["message"]
        return Task(when, message)
    
    def formatted(self, tz: timezone):
        return f"On {self.getWhen().astimezone(tz).strftime(_FORMAT)}:"
    
    def getWhen(self):
        return self.when
    
    def getMessage(self):
        return self.message
    
    async def tick(self, now: dt.datetime):
        if now >= self.when:
            self.kill = True
            return self.fire()
        return False
    
    def fire(self):
        return self.message

    def cancel(self):
        self.kill = True

class Recur(Task):
    def __init__(self, when: dt.datetime, message: str, interval: str):
        super().__init__(when, message)
        self.interval = interval
    
    def asjson(self):
        obj = super().asjson()
        obj["interval"] = self.interval
        return obj
    
    @staticmethod
    def fromjson(obj: dict[str, Union[str, int]]):
        when = dt.datetime.fromisoformat(obj["when"])
        message = obj["message"]
        interval = obj["interval"]
        return Recur(when, message, interval)
    
    def formatted(self, tz: timezone):
        return f"On {self.getWhen().astimezone(tz).strftime(_FORMAT)}; reschedule {self.interval}:"
    
    async def tick(self, now: dt.datetime):
        if now >= self.when:
            if self.interval == YEARLY:
                self.when = self.when.replace(year=now.year + 1)
            elif self.interval == MONTHLY:
                if now.month == 12:
                    self.when = self.when.replace(year=now.year + 1, month=1)
                else:
                    self.when = self.when.replace(month=now.month + 1)
            elif self.interval == WEEKLY:
                self.when += dt.timedelta(days=7)
            elif self.interval == DAILY:
                self.when += dt.timedelta(days=1)
            elif self.interval == HOURLY:
                self.when += dt.timedelta(hours=1)
            return self.fire()

class Taskmaster:
    def __init__(self):
        self.taskLists: dict[int, list[Task]] = {}
    
    def asjson(self):
        obj = {}
        for userID in self.taskLists:
            tasks = self.taskLists[userID]
            obj[str(userID)] = [task.asjson() for task in tasks]
        return obj
    
    @staticmethod
    def fromjson(obj: dict[str, list[dict[str, Union[int, str]]]]):
        tm = Taskmaster()
        for userID in obj:
            tasks = []
            typ: Optional[type[Task]] = None
            for taskObj in obj[userID]:
                if "interval" in taskObj:
                    typ = Recur
                else:
                    typ = Task
                tasks.append(typ.fromjson(taskObj))
            tm.taskLists[int(userID)] = tasks
        return tm
    
    async def update(self, time: dt.datetime) -> dict[int, list[str]]:
        messages: dict[int, list[str]] = {}
        outerIndex = 0
        userIDs = list(self.taskLists.keys())

        while outerIndex < len(userIDs):
            userID = userIDs[outerIndex]
            index = 0
            tasks = self.taskLists[userID]

            while index < len(tasks):
                task = tasks[index]
                fired = await task.tick(time)
                if fired:
                    if not messages.get(userID):
                        messages[userID] = []
                    messages[userID].append(fired)
                if task.kill:
                    index -= 1
                    tasks.remove(task)
                index += 1
            
            if not tasks:
                outerIndex -= 1
                self.taskLists.pop(userID)
                userIDs.remove(userID)
            outerIndex += 1
        
        return messages
    
    def addTask(self, task: Task, userID: int):
        if not self.taskLists.get(userID):
            self.taskLists[userID] = []
        self.taskLists[userID].append(task)
    
    def getTasks(self, userID: int):
        return self.taskLists.get(userID)
        