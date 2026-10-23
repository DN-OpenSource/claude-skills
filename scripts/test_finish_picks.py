"""product-visionary finishes every pick decided in the session before it ends.

Run: python -m pytest scripts/test_finish_picks.py -q
"""
from pathlib import Path

SKILL = (Path(__file__).resolve().parent.parent / "skills" / "product-visionary" / "SKILL.md").read_text(encoding="utf-8")


def test_finish_positive_every_pick_reaches_an_end_state():
    assert "**Finish today's picks:**" in SKILL
    assert "`failed` after 3 tries) before the session ends" in SKILL


def test_finish_positive_unproven_item_is_retried_then_session_goes_on():
    assert "up to 3 tries" in SKILL and "go on to\n   the next pick" in SKILL


def test_finish_negative_an_unproven_item_no_longer_ends_the_loop():
    assert "an item in the batch couldn't be proven" not in SKILL
    assert 'ask "continue?"' in SKILL  # named as forbidden, not as a step
