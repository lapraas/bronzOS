
from typing import Union
from utils import handlePaginationReaction
from CogTask import CogTask, TaskException
import datetime as dt
import discord
from discord.ext import commands
import os

from Help import Help
from Taskmaster import Taskmaster

def determinePrefix(bot: commands.Bot, message: discord.Message):
    if isinstance(message.channel, discord.DMChannel):
        if message.content.startswith("bel."):
            return "bel."
        return ""
    else:
        return "bel."

client = commands.Bot(
    command_prefix=determinePrefix,
    case_insensitive=True,
    help_command=Help(verify_checks=False)
)
taskmaster = Taskmaster()
cogTask = CogTask(taskmaster)
client.add_cog(cogTask)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}.")

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    await client.process_commands(message)

@client.event
async def on_reaction_add(reaction: discord.Reaction, user: Union[discord.User, discord.Member]):
    if user.bot: return
    await handlePaginationReaction(reaction, user)

@client.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"You missed a required argument `{error.param.name}`.")
    elif isinstance(error, commands.BadUnionArgument):
        await ctx.send(f"There was an error converting the argument `{error.param.name}`.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"This command does not exist!")
    elif isinstance(error, commands.CommandInvokeError):
        error = error.original
        if isinstance(error, TaskException):
            await ctx.send(error.message)
        else:
            await ctx.send("An unexpected error occurred.")
            raise error
    else:
        await ctx.send("An unexpected error occurred.")
        raise error

@client.check
async def globalCheck(ctx: commands.Context):
    channelName = ctx.channel.name if not isinstance(ctx.channel, discord.DMChannel) else "DM"
    print(f"[{str(dt.datetime.now().time())[:-7]}, #{channelName}] {ctx.message.author.name}: {ctx.message.content}")
    return True

client.run(os.getenv("DISCORD_SECRET_BRONZOS"))