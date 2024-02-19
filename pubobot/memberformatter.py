import discord
from typing import List, OrderedDict


def format_list(players: List[discord.Member], ranks: List[str], mention=False):
    if mention:
        return _format_list_mentioned(players, ranks)
    else:
        return _format_list(players, ranks)


def _format_list(players: List[discord.Member], ranks: List[str]):
    escaped_names = [
        (player.nick if player.nick else player.name).replace("`", r"\`")
        for player in players
    ]
    player_names = ", ".join(escaped_names)
    return player_names


def _format_list_mentioned(players: List[discord.Member], ranks: List[str]):
    return ", ".join([player.mention for player in players])


def format_team(prefix: str, players: List[discord.Member], ranks: List[str], mention=False):
    team = format_list(players, ranks, mention)
    return f"{prefix} {team}"


def format_unpicked(prefix: str, unpicked: OrderedDict):
    return "Unpicked: " + ", ".join(
        [f"{k}. {v.nick if v.nick else v.name}" for k, v in unpicked.items()]
    )
