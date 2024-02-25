#!/usr/bin/python2
# encoding: utf-8
import discord
import traceback
import time
from . import console, config, bot, stats3


ready = False
send_queue = []


def init():
    global ready, send_queue
    ready = False
    send_queue = []


def process_connection():
    global ready

    console.display("SYSTEM| Logged in as: {0}, ID: {1}".format(c.user.name, c.user.id))

    channels = stats3.get_channels()
    for cfg in channels:
        discord_channel = c.get_channel(cfg["channel_id"])
        if discord_channel == None:
            console.display(
                "SYSTEM| Could not find channel '{0}>{1}#' with CHANNELID '{2}'! Scipping...".format(
                    cfg["server_name"], cfg["channel_name"], cfg["channel_id"]
                )
            )
            # todo: delete channel
        else:
            chan = bot.Channel(discord_channel, cfg)
            bot.channels.append(chan)
            console.display(
                "SYSTEM| '{0}>{1}#' channel init successfull".format(
                    chan.cfg["server_name"], chan.cfg["channel_name"]
                )
            )
    ready = True


def get_empty_servers():
    for serv in c.guilds:
        n = 0
        for chan in serv.channels:
            if chan.id in [i.cfg["channel_id"] for i in bot.channels]:
                n = 1
                break
        if not n:
            console.display("server name: {0}, id: {1}".format(serv.name, serv.id))


async def send():  # send messages in queue
    global send_queue
    if len(send_queue):
        for func, kwargs in send_queue:
            try:
                await func(**kwargs)
            except Exception as e:
                console.display(
                    "ERROR| could not send data ({0}). {1}".format(str(func), str(e))
                )
        send_queue = []


async def close():  # on quit
    if c.is_closed():
        try:
            await c.logout()
            print("Successfully logged out.")
        except Exception as e:
            print("Error on logging out. {0}".format(str(e)))
    else:
        print("Connection is allready closed.")


### api for bot.py ###
def find_role_by_name(channel, name):
    name = name.lower()
    server = c.get_guild(channel.guild.id)
    if server:
        for role in server.roles:
            if name == role.name.lower():
                return role
    return None


def find_role_by_id(channel, role_id):
    server = c.get_guild(channel.guild.id)
    if server:
        for role in server.roles:
            if role_id == role.id:
                return role
    return None


async def edit_role(role, **fields):
    await role.edit(**fields)


async def remove_roles(member, *roles):
    await member.remove_roles(*roles)


async def add_roles(member, *roles):
    await member.add_roles(*roles)


def notice(channel, msg):
    console.display("SEND| {0}> {1}".format(channel.name, msg))
    send_queue.append([channel.send, {"content": msg}])


def reply(channel, member, msg):
    console.display(
        "SEND| {0}> {1}, {2}".format(channel.name, member.nick or member.name, msg)
    )
    send_queue.append([channel.send, {"content": "<@{0}>, {1}".format(member.id, msg)}])


def private_reply(member, msg):
    console.display("SEND_PM| {0}> {1}".format(member.name, msg))
    send_queue.append([member.send, {"content": msg}])


def delete_message(msg):
    send_queue.append([msg.delete, {}])


def edit_message(msg, new_content):
    console.display("EDIT| {0}> {1}".format(msg.channel.name, new_content))
    send_queue.append([msg.edit, {"content": new_content}])


def add_reaction(msg, emoji):
    send_queue.append([msg.add_reaction, {"emoji": emoji}])


def get_member_by_nick(channel, nick):
    server = c.get_guild(channel.guild.id)
    return discord.utils.find(lambda m: m.name == nick, server.members)


def get_member_by_id(channel, highlight):
    memberid = highlight.lstrip("<@!").rstrip(">")
    if memberid.isdigit():
        memberid = int(memberid)
        server = c.get_guild(channel.guild.id)
        return discord.utils.find(lambda m: m.id == memberid, server.members)
    else:
        return None


def create_client(loop=None):
    ### discord events ###
    intents = discord.Intents.default()
    intents.presences = True
    intents.members = True
    intents.typing = False
    c = discord.Client(intents=intents, loop=loop)

    @c.event
    async def on_ready():
        global ready
        if not ready:
            process_connection()
            ready = True
        else:
            console.display("DEBUG| Unexpected on_ready event!")
        await c.change_presence(activity=discord.Game(name="pm !help"))

    @c.event
    async def on_message(message):
        # if message.author.bot:
        # return
        if (
            isinstance(message.channel, discord.abc.PrivateChannel)
            and message.author.id != c.user.id
        ):
            console.display(
                "PRIVATE| {0}>{1}>{2}: {3}".format(
                    message.guild,
                    message.channel,
                    message.author.display_name,
                    message.content,
                )
            )
            private_reply(message.author, config.cfg.HELPINFO)
        elif message.content == "!enable_pickups":
            if message.channel.permissions_for(message.author).manage_channels:
                if message.channel.id not in [x.id for x in bot.channels]:
                    newcfg = stats3.new_channel(
                        message.guild.id,
                        message.guild.name,
                        message.channel.id,
                        message.channel.name,
                        message.author.id,
                    )
                    bot.channels.append(bot.Channel(message.channel, newcfg))
                    reply(
                        message.channel, message.author, config.cfg.FIRST_INIT_MESSAGE
                    )
                else:
                    reply(
                        message.channel,
                        message.author,
                        "this channel allready have pickups configured!",
                    )
            else:
                reply(
                    message.channel,
                    message.author,
                    "You must have permission to manage channels to enable pickups.",
                )
        elif message.content == "!disable_pickups":
            if message.channel.permissions_for(message.author).manage_channels:
                for chan in bot.channels:
                    if chan.id == message.channel.id:
                        bot.delete_channel(chan)
                        reply(
                            message.channel,
                            message.author,
                            "pickups on this channel have been disabled.",
                        )
                        return
                reply(
                    message.channel,
                    message.author,
                    "pickups on this channel has not been set up yet!",
                )
            else:
                reply(
                    message.channel,
                    message.author,
                    "You must have permission to manage channels to disable pickups.",
                )
        elif message.content != "":
            for channel in bot.channels:
                if message.channel.id == channel.id:
                    try:
                        await channel.processmsg(message)
                    except:
                        console.display(
                            "ERROR| Error processing message: {0}".format(
                                traceback.format_exc()
                            )
                        )

    @c.event
    async def on_member_update(before, after):
        # console.display("DEBUG| {0} changed status from {1}  to -{2}-".format(after.name, before.status, after.status))
        if str(after.status) in ["idle", "offline"]:
            bot.update_member(after)

    @c.event
    async def on_member_remove(member):
        bot.member_left(member)

    @c.event
    async def on_reaction_add(reaction, user):
        if reaction.message.id in bot.waiting_reactions.keys():
            bot.waiting_reactions[reaction.message.id]("add", reaction, user)

    @c.event
    async def on_reaction_remove(reaction, user):
        if reaction.message.id in bot.waiting_reactions.keys():
            bot.waiting_reactions[reaction.message.id]("remove", reaction, user)

    return c


c = create_client()


### connect to discord ###
def run():
    while True:
        try:
            if config.cfg.DISCORD_TOKEN != "":
                console.display("SYSTEM| logging in with token...")
                c.loop.run_until_complete(c.start(config.cfg.DISCORD_TOKEN))
            else:
                raise NotImplemented("Username/password authentication not supported.")
            c.loop.run_until_complete(c.connect())
        except KeyboardInterrupt:
            console.display("ERROR| Keyboard interrupt.")
            console.terminate()
            c.loop.run_until_complete(close())
            print("QUIT NOW.")
            break
        except Exception as e:
            console.display(
                "ERROR| Disconnected from the server: "
                + str(e)
                + "\nReconnecting in 15 seconds..."
            )
            time.sleep(15)
