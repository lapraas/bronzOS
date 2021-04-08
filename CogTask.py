
import discord
from discord.ext import commands, tasks as dasks
import datetime as dt
import json
from pytz import UnknownTimeZoneError, timezone
from typing import Optional

from Taskmaster import Event, Parser, Taskmaster, TaskException

UTC = timezone("UTC")

_TZ_GUIDE = "A valid time zone is something like `America/Chicago`. It's advised not to use abbreviations like EST, since those don't account for daylight savings time and one abbreviation can represent multiple time zones. For a list of valid timezones, check the entries of the \"TZ database name\" column on this Wikipedia page: <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>."
_FORMAT = "%I:%M:%S%p, %b %d (%a), %Y"

class S:
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
    

class CogTask(commands.Cog, name=S.COG.NAME, description=S.COG.DESC):
    def __init__(self, taskmaster: Optional[Taskmaster]):
        self.taskmaster = Taskmaster() if not taskmaster else taskmaster
        with open(S.PATH.TZPREFS, "r") as f:
            self.tzprefs: dict[str, str] = json.load(f)
        
        self.update.start()
    
    @dasks.loop(seconds=1)
    async def update(self):
        time = dt.datetime.now(UTC)
        await self.taskmaster.update(time)
    
    @staticmethod
    async def sendAlert(user: discord.User, alert: str):
        await user.send(S.INFO.ALERT(alert))
    
    @commands.group(aliases=["c"], invoke_without_command=True)
    async def create(self, ctx: commands.Context, *, args: str):
        if not ctx.invoked_subcommand:
            raise TaskException(S.ERR.INVALID_SUBCOMMAND(args[0]))
    
    @create.command(aliases=["e"])
    async def event(self, ctx: commands.Context, *args: str):
        if not args:
            raise TaskException(S.ERR.NO_ENTRY)
        
        parser = Parser(args)
        timezone = self.getTZForUser(ctx.author)
        if not timezone:
            raise TaskException(S.ERR.NO_TZ)
        eventTime = parser.getTimeFromToday(dt.datetime.now(timezone))
        message = parser.getMessage()
        
        task = Event(eventTime.astimezone(UTC), CogTask.sendAlert, [ctx.author, message])
        self.taskmaster.addTask(task)
        await ctx.send(S.INFO.EVENT_CREATED(eventTime.strftime(_FORMAT), message))
    
    def getTZForUser(self, user: discord.User):
        try:
            return timezone(self.tzprefs.get(str(user.id)))
        except UnknownTimeZoneError:
            return None

    @commands.command(aliases=["tz"])
    async def timezone(self, ctx: commands.Context, tz: Optional[str]=None):
        if not tz:
            tzObj = self.getTZForUser(ctx.author)
            if not tzObj:
                await ctx.send(S.INFO.TZ_USE_THIS)
            else:
                await ctx.send(S.INFO.TZ_USING(tzObj.zone))
            return
        try:
            tzObj = timezone(tz)
        except UnknownTimeZoneError:
            await ctx.send()
            return
        self.tzprefs[str(ctx.author.id)] = tz
        with open(S.PATH.TZPREFS, "w") as f:
            json.dump(self.tzprefs, f)
        await ctx.send(S.INFO.TZ_SUCCESS(tzObj.zone))

    @commands.command()
    async def now(self, ctx: commands.Context):
        tzObj = self.getTZForUser(ctx.author)
        if not tzObj:
            await ctx.send(S.ERR.NO_TZ)
        else:
            now = dt.datetime.now(tzObj)
            await ctx.send(S.INFO.NOW(tzObj.zone, now.strftime(_FORMAT)))