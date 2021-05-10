from utils import utils, exceptions
from utils.help import EmbedHelpCommand
from utils.constants import r, TOKEN, ALT_TOKEN

import os
import sys

import discord
from discord.ext import commands


if r.get("shutdown") == "True":
    raise Exception("Shutting down")


keys = {
"TOKEN": TOKEN,
"ALT_TOKEN": ALT_TOKEN
}


bot = commands.Bot(
    command_prefix=utils.determine_prefix,
    description="Help for GamerBot commands",
    intents=discord.Intents.all(),
    case_insensitive=True,
    help_command=EmbedHelpCommand(),
    allowed_mentions=discord.AllowedMentions.none()
)


for file in os.listdir("bot/cogs"):
    if file.endswith(".py"):
        fileName = file[:-3]
        bot.load_extension(f"cogs.{fileName}")




bot.run(keys[sys.argv[1]])
