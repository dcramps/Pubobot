import re

from io import StringIO

from typing import TypeVar, Dict, Iterable, Tuple, Callable

T = TypeVar("T")


def simple_match(expr: str, string: str):
    regex = compile_simple_expression(expr)
    return regex.match(string)


def simple_search(expr: str, string: str):
    regex = compile_simple_expression(expr)
    return regex.search(string)


def compile_simple_expression(expr: str) -> re.Pattern:
    """Compile a simplified expression into a regular expression.

    If you use f-strings, you must use `{{` and `}}` around capture groups,
    otherwise Python will interpolate.

    >>> pattern = compile_simple_expression("**{name}** [{current}/{total}]")
    >>> match = pattern.match("**elim** [1/8]")
    >>> match["name"]
    "elim"
    >>> match["current"]
    "1"
    >>> match["total"]
    "8"
    """
    pattern = StringIO()
    capture_pattern = re.compile(r"{\s*(?P<name>[a-zA-Z0-9_][a-zA-Z0-9_-]*)\s*}")

    pos = 0
    for match in capture_pattern.finditer(expr):
        name = match["name"]
        capture_group = f"(?P<{name}>.*?)"

        pattern.write(re.escape(expr[pos : match.start()]))
        pattern.write(capture_group)

        pos = match.end()

    if pos < len(expr):
        pattern.write(re.escape(expr[pos:]))

    return re.compile(pattern.getvalue())


class Match:
    def __init__(self, m: Dict[str, str]):
        self.m = m


def match_field(typ, key):
    """Return a property getter that returns `self.m[key]` converted to `typ`."""

    def getter(self: Match):
        return typ(self.m[key])

    return property(getter)


class PickStageMatch(Match):
    def __init__(
        self,
        match: Dict[str, str],
        alpha_team: Iterable[str],
        beta_team: Iterable[str],
        unpicked: Iterable[Tuple[int, str]],
    ):
        super().__init__(match)
        self.alpha_team = alpha_team
        self.beta_team = beta_team
        self.unpicked = list(unpicked)

    match_id = match_field(int, "match")
    turn_capt_id = match_field(int, "turn_capt_id")


class PickStageStartMatch(PickStageMatch):
    alpha_capt_id = match_field(int, "alpha_capt_id")
    beta_capt_id = match_field(int, "beta_capt_id")
    alpha_emote = match_field(str, "alpha_emote")
    alpha_capt_name = match_field(str, "alpha_capt_name")
    beta_emote = match_field(str, "beta_emote")
    beta_capt_name = match_field(str, "beta_capt_name")


class PickStageReadyMatch(Match):
    def __init__(
        self, match: Dict[str, str], alpha_team: Iterable[int], beta_team: Iterable[int]
    ):
        super().__init__(match)
        self.alpha_team = alpha_team
        self.beta_team = beta_team

    match_id = match_field(int, "match")


class PickStageMatcher:
    _start_header = compile_simple_expression(
        "__*({match_id})* **{game}** pickup has been started!__\r\n"
        "<@{alpha_capt_id}> and <@{beta_capt_id}> please start picking teams.\r\n\r\n"
    )

    _body = compile_simple_expression(
        "**Match {match_id}**\n"
        ":{alpha_emote}: \u2772{alpha_team}\u2773\n"
        ":{beta_emote}: \u2772{beta_team}\u2773\n\n"
        "__Unpicked__:\n"
        "[{unpicked}]"
    )

    _start_footer = compile_simple_expression("\r\n<@{turn_capt_id}> picks first!")
    _turn_footer = compile_simple_expression("\n<@{turn_capt_id}>'s turn to pick!")

    _picked = compile_simple_expression("`{name}`")
    _unpicked = compile_simple_expression("{num}. `{name}`")

    _ready = compile_simple_expression(
        "**TEAMS READY - Match {match_id}**\r\n\r\n"
        ":{alpha_emote}: \u2772{alpha_team}\u2773 \n"
        ":{beta_emote}: \u2772{beta_team}\u2773 \r\n\r\n"
    )

    _ready_member = compile_simple_expression("<@{id}>")

    def match_start(self, text: str) -> PickStageStartMatch:
        patterns = (self._start_header, self._body, self._start_footer)
        return self._match(text, PickStageStartMatch, patterns)

    def match_turn(self, text: str) -> PickStageMatch:
        patterns = (self._body, self._turn_footer)
        return self._match(text, PickStageMatch, patterns)

    def match_ready(self, text: str) -> PickStageReadyMatch:
        m = self._ready.match(text)
        if m is None:
            raise MatchError()

        fields = m.groupdict()
        alpha_team = self._match_ready_team(fields["alpha_team"])
        beta_team = self._match_ready_team(fields["beta_team"])
        return PickStageReadyMatch(fields, alpha_team, beta_team)

    def _match(
        self,
        text: str,
        factory: Callable[
            [Dict[str, str], Iterable[str], Iterable[str], Iterable[Tuple[int, str]]], T
        ],
        patterns: Iterable[re.Pattern],
    ) -> T:
        pos = 0
        fields = {}

        for pat in patterns:
            m = pat.match(text, pos)
            if m is None:
                raise MatchError()

            pos = m.end()
            fields.update(m.groupdict())

        alpha_team = self._match_picked(fields["alpha_team"])
        beta_team = self._match_picked(fields["beta_team"])
        unpicked = self._match_unpicked(fields["unpicked"])

        return factory(fields, alpha_team, beta_team, unpicked)

    def _match_picked(self, text: str) -> Iterable[str]:
        picked = []
        for match in self._picked.finditer(text):
            if not match:
                break

            name = match.group("name")
            picked.append(name)

        return picked

    def _match_unpicked(self, text: str) -> Iterable[Tuple[int, str]]:
        unpicked = []
        for s in text.split(","):
            match = self._unpicked.match(s.strip())
            assert match

            num, name = int(match.group("num")), match.group("name")
            unpicked.append((num, name))

        return unpicked

    def _match_ready_team(self, text: str) -> Iterable[int]:
        team = []
        for match in self._ready_member.finditer(text):
            if not match:
                break

            id = int(match.group("id"))
            team.append(id)

        return team


class MatchError(Exception):
    pass
