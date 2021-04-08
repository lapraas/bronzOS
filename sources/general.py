
from __future__ import annotations
from typing import Optional
import sources.ids as IDS

BOT_PREFIX = "bel."

MENTION_ME = f"<@{IDS.MY_USER_ID}>"
EMPTY = "\u200b"
NEWLINE = "\n"

BRONZOS_GRAPHIC_URL = "https://cdn.discordapp.com/attachments/284520081700945921/829501492939194378/bronzOS_logo.png"

stripLines = lambda text: "\n".join([line.strip() for line in text.split("\n")])
class Cmd:
    def __init__(self, *args, usage: list[str]=None, parent: Optional[Cmd]=None, **kwargs):
        self.name: str = args[0]
        self.aliases: list[str] = args[1:-1]
        self.desc: list[str] = args[-1]
        self.parent = parent
        self.qualifiedName = self.name
        if self.parent:
            self.qualifiedName = f"{parent.qualifiedName} {self.qualifiedName}"
        
        if usage:
            self.desc += "\n**Usage:**```\n" + "\n".join([f"{BOT_PREFIX}{self.qualifiedName} {case}" for case in usage]) + "```"
        
        for key, val in kwargs.items():
            setattr(self, key, val)
        
        self.desc = stripLines(self.desc)
        
        self.meta = {"name": self.name, "aliases": self.aliases, "help": self.desc}
        self.ref = f"{BOT_PREFIX}{self.name}"
        self.refF = f"`{self.ref}`"