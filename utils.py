
import discord
from discord.ext import commands
from typing import Optional, Union

from sources.general import EMPTY, BRONZOS_GRAPHIC_URL, stripLines
import sources.text as T

def getEmbed(title: str, description: str=None, fields: list[Union[tuple[str, str], tuple[str, str, bool]]]=None, imageURL: str=None, footer=None, url=None):
    """ Creates a custom embed. """
    
    if not description: description = ""
    if not fields: fields = []
    
    e = discord.Embed(
        title=title,
        description=stripLines(description),
        color=0x00C0FF,
        url=url
    )
    for field in fields:
        e.add_field(
            name=field[0],
            value=EMPTY if not len(field) >= 2 else field[1],
            inline=False if not len(field) == 3 else field[2]
        )
    if imageURL:
        e.set_image(url=imageURL)
    if footer:
        e.set_footer(text=footer)
    return e

def getBronzOSEmbed(title: str, description: str=None, fields: list[Union[tuple[str, str], tuple[str, str, bool]]]=None, imageURL: str=None, footer=None, url=None):
    e = getEmbed(title, description, fields, imageURL, footer, url)
    e.set_thumbnail(url=BRONZOS_GRAPHIC_URL)
    return e

class Page:
    def __init__(self, content: str=None, embed: Optional[discord.Embed]=None):
        self.content = content
        self.embed = embed
    
    def dump(self):
        return {
            "content": self.content,
            "embed": self.embed
        }

class Paginator:
    def __init__(self, pages: list[Page], issuerID: int, ignoreIndex: bool):
        self.pages = pages
        self.issuerID = issuerID
        self.ignoreIndex = ignoreIndex
        
        self.length = len(self.pages)
        self.focused = 0
        self.locked = False
        self.numbers = False
        
        if not self.ignoreIndex:
            for i, page in enumerate(pages):
                if not page.embed:
                    page.embed = discord.Embed(
                        title=EMPTY,
                        description=T.UTIL.paginationIndex(i + 1, self.length)
                    )
                else:
                    page.embed.set_footer(
                        text=T.UTIL.paginationIndex(i + 1, self.length)
                    )
    
    def lock(self):
        self.locked = True
    
    def unlock(self):
        self.locked = False
    
    def getReactions(self, isDM: bool):
        reactions = []
        amLarg = self.length > len(T.UTIL.indices)
        
        if self.numbers and not amLarg:
            reactions = T.UTIL.indices[:self.length]
        else:
            reactions = T.UTIL.arrows
        
        if not isDM and not amLarg:
            reactions.append(T.UTIL.switches[int(self.numbers)])
        
        return reactions
    
    def refocus(self, emoji: str):
        if emoji == T.UTIL.emojiFirst:
            self.focused = 0
        elif emoji == T.UTIL.emojiPrior and self.focused > 0:
            self.focused -= 1
        elif emoji == T.UTIL.emojiNext and self.focused < self.length - 1:
            self.focused += 1
        elif emoji == T.UTIL.emojiLast:
            self.focused = self.length - 1
            
        elif emoji in T.UTIL.indices:
            self.focused = T.UTIL.indices.index(emoji)
        elif emoji in T.UTIL.switches:
            # yes MasN this works how you think it does
            self.numbers = not self.numbers
        
        return self.getFocused()
    
    def getFocused(self):
        return self.pages[self.focused]

toListen: dict[int, Paginator] = {}
        
async def updatePaginatedMessage(message: discord.Message, user: discord.User, paginator: Paginator, emoji: Optional[str]=None):
    if not user.id == paginator.issuerID: return
    oldFocused = paginator.getFocused()
    focused = paginator.refocus(emoji)
    if not oldFocused is focused:
        await message.edit(content=focused.content, embed=focused.embed)
    isDM = isinstance(message.channel, discord.DMChannel)
    if emoji in T.UTIL.switches and not isDM:
        newReactions = paginator.getReactions(isDM)
        await message.clear_reactions()
        for reaction in newReactions:
            await message.add_reaction(reaction)
    elif emoji == None:
        newReactions = paginator.getReactions(isDM)
        for reaction in newReactions:
            await message.add_reaction(reaction)
        

async def paginate(ctx: commands.Context, contents: list[dict[str, Union[str, discord.Embed]]], ignoreIndex: bool=False):
    pages = []
    for page in contents:
        pages.append(Page(**page))
    if not pages:
        raise IndexError("No messages were given to the pagination function")
    
    paginator = Paginator(pages, ctx.author.id, ignoreIndex)
    focused = paginator.getFocused()
    message: discord.Message = await ctx.send(content=focused.content, embed=focused.embed)
    if len(pages) == 1: return
    toListen[message.id] = paginator
    await updatePaginatedMessage(message, ctx.author, paginator)

async def handlePaginationReaction(reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
    if not reaction.message.id in toListen:
        return
    paginator = toListen[reaction.message.id]
    
    emoji = str(reaction.emoji)
    await updatePaginatedMessage(reaction.message, user, paginator, emoji)
    if not isinstance(reaction.message.channel, discord.DMChannel):
        await reaction.remove(user)
