
import discord
from discord.ext import commands, tasks as dasks
import datetime as dt
import json
from pytz import UnknownTimeZoneError, timezone
from typing import Optional

from sources.general import _FORMAT
import sources.text as T
from Taskmaster import Task, Parser, Taskmaster, TaskException

S = T.TASK
UTC = timezone("UTC")

class CogTask(commands.Cog, name=S.COG.NAME, description=S.COG.DESC):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open(S.PATH.TASKMASTER, "r") as f:
            self.taskmaster = Taskmaster.fromjson(json.load(f))
        with open(S.PATH.TZPREFS, "r") as f:
            self.tzprefs: dict[str, str] = json.load(f)
        
        self.update.start()

    def writeTaskmaster(self):
        with open(S.PATH.TASKMASTER, "w") as f:
            json.dump(self.taskmaster.asjson(), f)
    
    @dasks.loop(seconds=1)
    async def update(self):
        time = dt.datetime.now(UTC)
        messages = await self.taskmaster.update(time)
        if messages:
            for userID in messages:
                user = await self.bot.fetch_user(userID)
                for message in messages[userID]:
                    await user.send(S.INFO.ALERT(message))
                    print(f"[{str(dt.datetime.now().time())[:-7]}] Task for {user.name} triggered: {message}")
            self.writeTaskmaster()
    
    @commands.command(**S.CREATE.meta)
    async def create(self, ctx: commands.Context, *, args: str):
        if not args:
            raise TaskException(S.ERR.NO_ENTRY)
        
        parser = Parser(args.split(" "))
        userTZ = self.getTZForUser(ctx.author.id)
        if not userTZ:
            raise TaskException(S.ERR.NO_TZ)
        task = parser.getAsTask(dt.datetime.now())
        self.taskmaster.addTask(task, ctx.author.id)
        self.writeTaskmaster()
        await ctx.send(S.INFO.TASK_CREATED(task.getWhen().astimezone(userTZ).strftime(_FORMAT), parser.getMessage()))
    
    def getTasksOrFail(self, userID: int):
        tasks = self.taskmaster.getTasks(userID)
        if not tasks:
            raise TaskException(S.ERR.NO_TASKS)
        return tasks
    
    def getTZForUser(self, userID: int):
        try:
            return timezone(self.tzprefs.get(str(userID)))
        except UnknownTimeZoneError:
            return None
    
    def getTZForUserOrFail(self, userID: int):
        tz = self.getTZForUser(userID)
        if not tz:
            raise TaskException(S.ERR.NO_TZ)
        return tz

    @commands.command(**S.TASKS.meta)
    async def tasks(self, ctx: commands.Context):
        tasks = sorted(self.getTasksOrFail(ctx.author.id), key=lambda event: event.when)
        tz = self.getTZForUserOrFail(ctx.author.id)
        toSend = S.INFO.TASKS_HEADER + "```\n"
        digits = len(str(len(tasks)))
        for i, task in enumerate(tasks):
            i = str(i + 1)
            spacing = (digits - len(i)) * " "
            toSend += S.INFO.TASKS(i, spacing, task.formatted(tz), task.getMessage())
        toSend += "```"
        await ctx.send(toSend)
    
    @commands.command(**S.REMOVE.meta)
    async def remove(self, ctx: commands.Context, index: int):
        tasks = self.getTasksOrFail(ctx.author.id)
        if index > len(tasks):
            raise TaskException(S.ERR.REMOVE_OOB(index, len(tasks)))
        task = tasks.pop(index - 1)
        self.writeTaskmaster()
        await ctx.send(S.INFO.REMOVE_SUCCESS(str(index), task.getMessage()))

    @commands.command(**S.TIMEZONE.meta)
    async def timezone(self, ctx: commands.Context, tz: Optional[str]=None):
        if not tz:
            tzObj = self.getTZForUser(ctx.author.id)
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

    @commands.command(**S.NOW.meta)
    async def now(self, ctx: commands.Context):
        tzObj = self.getTZForUser(ctx.author.id)
        if not tzObj:
            raise TaskException(S.ERR.NO_TZ)
        else:
            now = dt.datetime.now(tzObj)
            await ctx.send(S.INFO.NOW(tzObj.zone, now.strftime(_FORMAT)))