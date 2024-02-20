import re

from typing import TypeVar, Dict, Iterable, Tuple

T = TypeVar("T")


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
    _start_header = re.compile(
        r"__\*\((?P<match_id>\d+)\)\* \*\*elim\*\* pickup has been started!__\s+"
        r"<@(?P<alpha_capt_id>\d+)> and <@(?P<beta_capt_id>\d+)> please start picking teams.\s+"
    )

    _body = re.compile(
        r"\*\*Match (?P<match_id>\d+)\*\*\s+"
        r":(?P<alpha_emote>[^:]+): \u2772(?P<alpha_team>[^\u2773]+)\u2773\s+"
        r":(?P<beta_emote>[^:]+): \u2772(?P<beta_team>[^\u2773]+)\u2773\s+"
        r"__Unpicked__:\s+\[(?P<unpicked>[^]]+)\]\s+"
    )

    _start_footer = re.compile(r"<@(?P<turn_capt_id>\d+)> picks first!")
    _turn_footer = re.compile(r"<@(?P<turn_capt_id>\d+)>'s turn to pick!")
    _picked = re.compile(r"`(?P<name>[^`]+)`")
    _unpicked = re.compile(r"(?P<num>\d+)\. `(?P<name>[^`]+)`")

    _ready = re.compile(
        r"\*\*TEAMS READY - Match (?P<match_id>\d+)\*\*\s+"
        r":(?P<alpha_emote>[^:]+): \u2772(?P<alpha_team>[^\u2773]+)\u2773\s+"
        r":(?P<beta_emote>[^:]+): \u2772(?P<beta_team>[^\u2773]+)\u2773\s+"
    )

    _ready_member = re.compile(r"<@(?P<id>\d+)>")

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

    def _match(self, text: str, cls: T, patterns: Iterable[re.Pattern]) -> T:
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

        return cls(fields, alpha_team, beta_team, unpicked)

    def _match_picked(self, text: str) -> Iterable[Tuple[str]]:
        pos = 0

        picked = []
        while pos < len(text):
            match = self._picked.search(text, pos)
            if not match:
                break

            name = match.group("name")
            picked.append(name)
            pos = match.end()

        return picked

    def _match_unpicked(self, text: str) -> Iterable[Tuple[int, str]]:
        pos = 0

        unpicked = []
        while pos < len(text):
            match = self._unpicked.search(text, pos)
            if not match:
                break

            num, name = int(match.group("num")), match.group("name")
            unpicked.append((num, name))
            pos = match.end()

        return unpicked

    def _match_ready_team(self, text: str) -> Iterable[int]:
        pos = 0

        team = []
        while pos < len(text):
            match = self._ready_member.search(text, pos)
            if not match:
                break

            id = int(match.group("id"))
            team.append(id)
            pos = match.end()

        return team


class MatchError(Exception):
    pass
