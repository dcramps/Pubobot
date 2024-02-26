import discord
from typing import List, OrderedDict, Dict, Tuple

## No decorations
def format_list(players: List[discord.Member], mention = False) -> str:
    return format_list_tuples([(player, None) for player in players], mention)

## Yes decorations
def format_list_tuples(players: List[Tuple[discord.Member, List[str]]], mention = False) -> str:
    escaped_names = [get_player_string(player, mention) for player in players]
    return ", ".join(escaped_names)

def format_unpicked(prefix: str, unpicked: OrderedDict):
    return "Unpicked: " + ", ".join(
        [f"{k}. {v.nick if v.nick else v.name}" for k, v in unpicked.items()]
    )

### Utility Functions

def get_player_string(player: Tuple[discord.Member, List[str]], mention) -> str:
    mention_or_name = f"<@{player[0].id}>" if mention else get_player_name(player[0])
    decorations = get_decorations(player[1])
    if decorations is not None:
        return f"{mention_or_name} {decorations}"
    else:
        return f"{mention_or_name}"

def get_player_name(player: discord.Member) -> str:
    return (player.nick if player.nick else player.name).replace("`", r"\`")

def get_decorations(decorations: List[str]):
    if decorations is None or not len(decorations):
        return None
    return f"[{', '.join(decorations)}]"