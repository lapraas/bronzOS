
from sources.general import BOT_PREFIX, NEWLINE, stripLines, BOT_PREFIX as lap

cogEmbed = lambda cogName, cogDescription, commandNames: {
    "title": cogName,
    "description": f"""
        {cogDescription}
        
        Use `lap.help commandName` to get help with a specific command.
        ```
        {NEWLINE.join(commandNames)}```
    """
}

commandEmbed = lambda cmdName, cmdAliases, cmdDesc: {
    "title": f"`{BOT_PREFIX}{cmdName}`",
    "description": f"""
        {("also `" + "`, `".join(cmdAliases) + "`") if cmdAliases else ""}
        
        {cmdDesc}
    """
}

commandEmbedWithFooter = lambda cmdName, cmdAliases, cmdDesc, cogName: {
    ** commandEmbed(cmdName, cmdAliases, cmdDesc),
    **{
        "footer": f"This command is part of the {cogName}."
    }
}

indices = lambda names, index: NEWLINE.join([(f"**    -> **" if i == index else f"{i+1}. ") + f"`{name}`" for i, name in enumerate(names)])
commandPaginationContent = lambda parentName, names, index, parentAliases=None: stripLines(f"""
    **Commands for `{parentName}`**{"" if not parentAliases else (f"{NEWLINE}also `" + "`, `".join(parentAliases) + f"`{NEWLINE}")}
    {indices(names, index)}
""")
cogPaginationContent = lambda names, index: stripLines(f"""
    **List of bot cogs**
    Use `{lap}help (cog name)` for a more detailed list of commands for a certain cog. Note that the cog name is case-sensitive.
    
    {indices(names, index)}
""")
