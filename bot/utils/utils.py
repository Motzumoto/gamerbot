from utils import exceptions
from utils.constants import command_prefix, r, REPORTS, embedColors, regions, teams

import discord
from discord.ext import commands
from discord.utils import get

from discord import Webhook, AsyncWebhookAdapter
import aiohttp

import asyncio

import json

import redis

from datetime import datetime
import pytz
from pytz import timezone, utc


def saveData(r, key, value):
    rval = json.dumps(value)
    r.set(key, rval)


def loadGuildInfo(r):
    rval = r.get("guildInfo")
    tempGuildInfo = json.loads(rval)
    guildInfo = {}

    for g in tempGuildInfo:
        guildInfo[int(g)] = tempGuildInfo[g]

    return guildInfo


def determine_prefix(bot, ctx, clean=False):
    guildInfo = loadGuildInfo(r)
    guild = ctx.guild
    if guild:
        prefix = guildInfo[guild.id].get('prefix')
    else:
        prefix = command_prefix

    if clean == False:
        prefix = commands.when_mentioned_or(*prefix)(bot, ctx)

    return prefix


def loadBlacklisted(r):
    blackListed = r.lrange("blacklisted", 0, -1)
    for i in range(0, len(blackListed)):
        blackListed[i] = int(blackListed[i].decode("utf-8"))

    return blackListed


def loadTrackingGuilds(r):
    rval = r.get("trackingGuilds")
    tempTrackingGuilds = json.loads(rval)
    trackingGuilds = {}

    for t in tempTrackingGuilds:
        trackingGuilds[int(t)] = tempTrackingGuilds[t]
        for u in trackingGuilds[int(t)]:
            index = trackingGuilds[int(t)].index(u)
            trackingGuilds[int(t)][index]['channel-id'] = int(trackingGuilds[int(t)][index]['channel-id'])

    return trackingGuilds


def loadCSGOLinks(r):
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
    return None


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


async def sendReport(ctx, message, *, embed=None):
    async with aiohttp.ClientSession() as cs:
        webhook = Webhook.from_url(REPORTS, adapter=AsyncWebhookAdapter(cs))
        await webhook.send(message, embed=embed)


async def getJSON(url, headers=None, json=True, read=False):
    async with aiohttp.ClientSession() as cs:
        async with cs.get(url, headers=headers) as data:
            if json:
                try:
                    data = await data.json()
                except aiohttp.ContentTypeError:
                    raise exceptions.EmbedError(title="Something went wrong!", description="The server returned an unexpected response. Please try again later.")

            elif read:
                data = await data.read()

            return data


def TimefromStamp(ts, region):
    region = str(region)
    if regions.get(region) != None:
        region = regions[region]
    d = ((datetime.fromtimestamp(ts)).astimezone(timezone(region))).strftime('%H:%M:%S %m/%d/%Y') + f" {region} Time"
    return d


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
        raise commands.BadArgument(f"Your server may not be setup for Game Events yet. Run {determine_prefix(ctx.bot, ctx)[-1]}setup")
    else:
        return True