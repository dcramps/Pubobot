import pytest

from typing import Tuple, List, Dict

from matcher import compile_simple_expression


ExprTestCase = Tuple[str, Dict[str, str]]


@pytest.mark.parametrize(
    "expr, pattern, testcases",
    [
        (
            "**{name}** [{current}/{total}]",
            r"\*\*(?P<name>.*?)\*\*\ \[(?P<current>.*?)/(?P<total>.*?)\]",
            [
                ("**elim** [0/8]", dict(name="elim", current="0", total="8")),
                (
                    "**capture the flag** [3/10]",
                    dict(name="capture the flag", current="3", total="10"),
                ),
            ],
        )
    ],
)
def test_compile_simple_expression(
    expr: str, pattern: str, testcases: List[ExprTestCase]
):
    regex = compile_simple_expression(expr)
    assert regex.pattern == pattern

    for text, expect in testcases:
        match = regex.match(text)

        assert match
        assert match.groupdict() == expect
