
import discord
from discord.ext import commands, tasks as dasks
import datetime as dt
import json
from pytz import UnknownTimeZoneError, timezone
from typing import Optional

import sources.text as T
from Taskmaster import Event, Parser, Taskmaster, TaskException

S = T.TASK
UTC = timezone("UTC")
_FORMAT = "%I:%M:%S%p, %b %d (%a), %Y"

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
    
    @commands.group(S.CREATE.meta, invoke_without_command=True)
    async def create(self, ctx: commands.Context, *, args: str):
        if not ctx.invoked_subcommand:
            raise TaskException(S.ERR.INVALID_SUBCOMMAND(args[0]))
    
    @create.command(S.EVENT.meta)
    async def event(self, ctx: commands.Context, *, args: str=None):
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

    @commands.command(S.TIMEZONE.meta)
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

    @commands.command(S.NOW.meta)
    async def now(self, ctx: commands.Context):
        tzObj = self.getTZForUser(ctx.author)
        if not tzObj:
            await ctx.send(S.ERR.NO_TZ)
        else:
            now = dt.datetime.now(tzObj)
            await ctx.send(S.INFO.NOW(tzObj.zone, now.strftime(_FORMAT)))