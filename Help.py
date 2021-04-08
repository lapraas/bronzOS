
from typing import Callable, Mapping, Optional, Union
from utils import getBronzOSEmbed, paginate
import discord
from discord.ext import commands

import sources.text as T

def getNonhiddenCommands(commands: list[commands.Command], getter: Callable[[commands.Command], Union[commands.Command, str]]=lambda x: x) -> list[Union[commands.Command, str]]:
    return [getter(command) for command in commands if not command.hidden]

class Help(commands.DefaultHelpCommand):
    async def send_bot_help(self, mapping: Mapping[Optional[commands.Cog], list[commands.Command]]):
        pages = []
        cogNames = [cog.qualified_name for cog in mapping if isinstance(cog, commands.Cog) and getNonhiddenCommands(mapping[cog])]
        for i, cog in enumerate(mapping):
            if not cog: continue
            cmds = mapping[cog]
            if not cmds: continue
            pages.append({
                "content": T.HELP.cogPaginationContent(cogNames, i),
                "embed": getBronzOSEmbed(**T.HELP.cogEmbed(cog.qualified_name, cog.description, getNonhiddenCommands(cmds, lambda cmd: cmd.qualified_name)))
            })
        await paginate(self.context, pages, True)
    
    async def sendPaginatedHelp(self, parentName: str, cmds: list[commands.Command], aliases: Optional[list[str]]=None):
        pages = []
        commandNames = [cmd.qualified_name for cmd in cmds]
        for i, command in enumerate(cmds):
            pages.append({
                "content": T.HELP.commandPaginationContent(parentName, commandNames, i, aliases),
                "embed": getBronzOSEmbed(**T.HELP.commandEmbed(command.qualified_name, command.aliases, command.help))
            })
        await paginate(self.context, pages, True)
    
    async def send_cog_help(self, cog: commands.Cog):
        await self.sendPaginatedHelp(cog.qualified_name, getNonhiddenCommands(cog.get_commands()))
    
    async def send_group_help(self, group: commands.Group):
        await self.sendPaginatedHelp(group.qualified_name, getNonhiddenCommands(group.commands), group.aliases)
    
    async def send_command_help(self, command: commands.Command):
        embed = getBronzOSEmbed(
            **T.HELP.commandEmbedWithFooter(command.qualified_name, command.aliases, command.help, command.cog_name)
        )
        await self.context.send(embed=embed)
