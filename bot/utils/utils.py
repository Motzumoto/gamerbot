if __name__ == "__main__":
    import exceptions
    from constants import command_prefix, teams, r, EnvVars, Regions
else:
    from utils import exceptions
    from utils.constants import command_prefix, teams, r, EnvVars, Regions

import discord
from discord.ext import commands
from discord.utils import get

from discord import Webhook, AsyncWebhookAdapter
import aiohttp

import json

from datetime import datetime
from dateutil import tz


def determine_prefix(bot, ctx, clean=False):
    guildInfo = loadGuildInfo()
    guild = ctx.guild
    if guild:
        prefix = guildInfo[guild.id].get('prefix')
    else:
        prefix = command_prefix

    if clean == False:
        prefix = commands.when_mentioned_or(prefix)(bot, ctx)

    return prefix


def saveData(key, value):
    rval = json.dumps(value)
    r.set(key, rval)


def loadGuildInfo():
    rval = r.get("guildInfo")
    tempGuildInfo = json.loads(rval)
    guildInfo = {}

    for g in tempGuildInfo:
        guildInfo[int(g)] = tempGuildInfo[g]

    return guildInfo


def loadBlacklisted():
    blackListed = r.lrange("blacklisted", 0, -1)
    for i in range(0, len(blackListed)):
        blackListed[i] = int(blackListed[i].decode("utf-8"))

    return blackListed


def loadTrackingGuilds():
    rval = r.get("trackingGuilds")
    tempTrackingGuilds = json.loads(rval)
    trackingGuilds = {}

    for t in tempTrackingGuilds:
        trackingGuilds[int(t)] = tempTrackingGuilds[t]
        for u in trackingGuilds[int(t)]:
            index = trackingGuilds[int(t)].index(u)
            trackingGuilds[int(t)][index]['channel-id'] = int(trackingGuilds[int(t)][index]['channel-id'])

    return trackingGuilds


def loadCSGOLinks():
    rval = r.get("csgoLinks")
    tempCsgoLinks = json.loads(rval)
    csgoLinks = {}

    for c in tempCsgoLinks:
        csgoLinks[int(c)] = int(tempCsgoLinks[c])

    return csgoLinks


def multi_key_dict_get(d : dict, k):
    for keys, v in d.items():
        if k in keys:
            return v


def convertBooltoStr(bool : bool):
    if bool == True:
        return "On"
    elif bool == False:
        return "Off"


def convertBooltoExpress(bool : bool):
    if bool == True:
        return "Yes"
    elif bool == False:
        return "No"


async def sendReport(message, *, embed=None):
    async with aiohttp.ClientSession() as cs:
        webhook = Webhook.from_url(EnvVars.REPORTS, adapter=AsyncWebhookAdapter(cs))
        message = sendLargeMessage(message)
        for m in message:
            await webhook.send(m, embed=embed)


def sendLargeMessage(message):
    message = str(message)
    new_message = []
    x = 0
    while x <= len(message):
        new_message.append(message[x:x+1000])
        x += 1000
    return new_message


async def getJSON(url, headers=None, json=True, read=False, proxies={}):
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url, headers=headers, proxy=proxies.get('http')) as data:
            if json:
                try:
                    data = await data.json()
                except aiohttp.ContentTypeError:
                    raise exceptions.EmbedError(title="Something went wrong!", description="The server returned an unexpected response. Please try again later.")

            elif read:
                data = await data.read()

            return data


def getTimeRegion(region):
    if isinstance(region, discord.VoiceRegion):
        region = region.name

    try:
        region = getattr(Regions, region)
    except AttributeError:
        pass

    return region


def TimefromStamp(ts, region):
    region = getTimeRegion(region)
    time = datetime.fromtimestamp(ts).astimezone(tz.gettz(region)).strftime('%H:%M:%S %m/%d/%Y') + f" {region} Time"
    return time


def UTCtoZone(utc_time, region):
    region = getTimeRegion(region)

    utc = tz.gettz('UTC')
    new_zone = tz.gettz(region)

    utc_time = utc_time.replace(tzinfo=utc)

    local_time = (utc_time.astimezone(new_zone)).strftime('%H:%M:%S %m/%d/%Y') + f" {region} Time"

    return local_time


def getHypixelHelp(dict : dict):
    help = ""
    for key, value in dict.items():
        if isinstance(key, tuple):
            help += key[0]
        elif isinstance(key, str):
            help += key
        help += ", "
    help = help[:-2]
    return help


def checkIfSetup(ctx):
    NotFound = None

    if not any("Events" in voicechannel.name for voicechannel in ctx.guild.voice_channels):
        NotFound = "main events voice channel"

    elif not all(get(ctx.guild.roles, name=team) for team in teams):
        NotFound = "team roles"

    elif not all(get(ctx.guild.voice_channels, name=team) for team in teams):
        NotFound = "team voice channels"

    elif not get(ctx.guild.roles, name="Banned from event"):
        NotFound = "Banned from event role"


    if NotFound:
        raise commands.BadArgument(f"Your server may not be setup for Game Events yet. Run {determine_prefix(ctx.bot, ctx, clean=True)}setup")
    else:
        return True


def insert_commas(num: int):
    return "{:,}".format(num)


def getRate(stat1 : int, stat2 : int):
    try:
        return round(stat1/stat2, 2)
    except ZeroDivisionError:
        return 0
