"""
TBO ArmaTracker

Licensed under the GNU General Public License
See license.md
"""
import asyncio
import datetime
import configparser
import json
import discord
from discord.ext import commands
import a2s


config = configparser.ConfigParser()
config.read("config.ini")

# Constants
BOT_TOKEN = config["Discord"]["key"]
SERVER_IP = config["ARMA"]["server_ip"]
SERVER_PORT = config["ARMA"]["server_port"]
MAINS_ID = config["Discord"]["channel"]
THUMBNAIL_URL = (
    "https://static.wixstatic.com/media/5474d8_6521e7baef3545a8a8c91b8a55726f7d~mv2.png"
    "v1/fill/w_98,h_86,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/TBOA3_logo_1.png"
)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=">", intents=intents)


async def get_server_info():
    """Query the ARMA Server for current status"""
    address = (SERVER_IP, SERVER_PORT)
    tbo = await a2s.ainfo(address)
    players = await a2s.aplayers(address)
    return tbo, players


@bot.event
async def on_ready():
    """Run these actions when the bot is fully online"""
    print("Trying purge + setup")
    creds = await load_json()
    channel = discord.Client.get_channel(bot, int(MAINS_ID))
    bootup = await channel.send("Booting the Bot")
    await channel.purge()
    ctx = await bot.get_context(bootup)
    await info_mesages(ctx)
    await channel.send(embed=await format_gtx_embed())
    await channel.send(embed=await format_ts_embed())
    await create_check(ctx, creds)


@bot.command()
async def clear(ctx, number: int = 10):
    """Manually nuke a channel, just in case"""
    await ctx.channel.purge(limit=number)


async def info_mesages(ctx):
    """Load the Logo"""
    logo = (
        "https://static.wixstatic.com/media/5474d8_4055ea615ebb452dbcbf5c7c30955d5b~mv2.jpg/"
        "v1/fill/w_582,h_107,al_c,q_80,usm_0.66_1.00_0.01,enc_auto/TBO_Arma_Header.jpg"
    )
    await ctx.send(logo)


async def format_server_embeds(tbo, creds):
    """Format the embed for the server status"""
    # Create server info embed
    server_embed = discord.Embed(
        title="TBO Servertracker 9001",
        url="https://theblackorder.wixsite.com/tbo-arma3/",
        description="Current Online Server",
        color=0x80FFFF,
    )
    server_embed.set_thumbnail(url=THUMBNAIL_URL)
    server_embed.add_field(name="Current Server", value=tbo.server_name, inline=False)
    if tbo.map_name:
        server_embed.add_field(name="Map", value=tbo.map_name, inline=False)
    server_embed.add_field(name="Address", value=SERVER_IP)
    server_embed.add_field(name="Port", value=tbo.port)

    creds_dict = {pair["name"]: pair["pwd"] for pair in creds}
    password = creds_dict.get(tbo.server_name)
    if password:
        server_embed.add_field(name="Password", value=password)

    return server_embed


async def format_player_embeds(players):
    """Format the embed for the player count"""
    # Create player info embed
    player_embed = discord.Embed(
        title="Online Players",
        url="https://theblackorder.wixsite.com/tbo-arma3/",
        description="Current Players Online",
        color=0x80FFFF,
    )
    player_embed.set_thumbnail(url=THUMBNAIL_URL)

    if players:
        for player in players:
            player_embed.add_field(
                name=player.name,
                value=datetime.timedelta(seconds=round(player.duration)),
                inline=False,
            )
    else:
        player_embed.add_field(name="No Players Online", value="", inline=False)
    return player_embed


async def format_gtx_embed():
    """Format the embed for the GTX Server Host"""
    gtx_embed = discord.Embed(
        title="GTX Gaming",
        url="https://www.gtxgaming.co.uk/",
        color=0x80FFFF,
    )
    gtx_embed.set_thumbnail(
        url="https://www.gtxgaming.co.uk/wp-content/uploads/2021/03/GTX-Logo.png"
    )
    gtx_embed.add_field(name="Player Slots", value="20")
    gtx_embed.add_field(name="Location", value="London, UK")
    gtx_embed.add_field(name="Memory", value="8 GB")
    gtx_embed.add_field(name="CPU", value="4.2 GHz (6 Cores/12 Threads)")
    gtx_embed.add_field(name="Disk Space", value="120 GB")
    return gtx_embed


async def format_ts_embed():
    """Format the embed for the TeamSpeak status"""
    ts_embed = discord.Embed(
        title="TeamSpeak",
        url="https://www.teamspeak.com/en/downloads/",
        color=0x80FFFF,
    )
    ts_embed.set_thumbnail(
        url="https://discourse-forums-images.s3.dualstack.us-east-2.amazonaws.com/"
        "original/2X/2/269d8bb30efc4bdf5c99f1f27c2aeadc1ca2fa5d.png"
    )
    ts_embed.add_field(name="Address", value="ts3l.gtxgaming.co.uk:10178")
    ts_embed.add_field(name="Password", value="tbo")
    return ts_embed


@bot.command()
async def create_check(ctx, creds):
    """Begin the looping check!"""
    tbo, players = await get_server_info()

    server_embed = await format_server_embeds(tbo, creds)
    checkmsg1 = await ctx.send(embed=server_embed)

    player_embed = await format_player_embeds(players)
    checkmsg2 = await ctx.send(embed=player_embed)

    while True:
        await asyncio.sleep(5)
        tbo, players = await get_server_info()

        server_embed = await format_server_embeds(tbo, creds)
        await checkmsg1.edit(embed=server_embed)

        player_embed = await format_player_embeds(players)
        await checkmsg2.edit(embed=player_embed)


async def load_json():
    """Load the latest server update file"""
    with open("server.json", encoding="UTF-8") as jfile:
        servers = json.load(jfile)
        return servers


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
