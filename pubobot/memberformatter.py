from typing import List, Tuple
from collections import OrderedDict

import discord


## No tags
def format_list(players: List[discord.Member], mention=False) -> str:
    return format_list_tuples([(player, None) for player in players], mention)


## Yes tags
def format_list_tuples(
    players: List[Tuple[discord.Member, List[str]]], mention=False
) -> str:
    escaped_names = [get_player_string(player, mention) for player in players]
    return ", ".join(escaped_names)


def format_unpicked(unpicked: OrderedDict):
    return ", ".join(
        [
            f"{k}. {get_player_string((v['player'], v.get('tags', [])), False)}"
            for k, v in unpicked.items()
        ]
    )


### Utility Functions


def get_player_string(player: Tuple[discord.Member, List[str]], mention) -> str:
    mention_or_name = f"<@{player[0].id}>" if mention else get_player_name(player[0])
    tags = get_tags(player[1])
    if tags is not None:
        return f"{mention_or_name} {tags}"
    else:
        return f"{mention_or_name}"


def get_player_name(player: discord.Member) -> str:
    return escaped_markdown((player.nick if player.nick else player.name))


def get_tags(tags: List[str]):
    if tags is None or not len(tags):
        return None
    return f"[{', '.join(tags)}]"


def escaped_markdown(input: str) -> str:
    return (
        input.replace("`", r"\`")
        .replace("_", r"\_")
        .replace("*", r"\*")
        .replace("#", r"\#")
    )
