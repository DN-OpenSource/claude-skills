"""test-report's video rules: record failures, keep recordings local, never commit them.

Run: python -m pytest scripts/test_test_report_video.py -q
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "test-report" / "SKILL.md"
VIDEO = ROOT / "skills" / "test-report" / "references" / "video.md"


def test_video_positive_skill_links_rules_and_report_has_video_column():
    s = SKILL.read_text(encoding="utf-8")
    assert "references/video.md" in s
    assert "| Result | Time | Video |" in s
    assert "local only" in s and "recording unavailable" in s


def test_video_positive_rules_cover_every_platform_and_safeguard():
    v = VIDEO.read_text(encoding="utf-8")
    for must in ("retain-on-failure", "Cypress", "adb shell screenrecord", "xcrun simctl io booted recordVideo",
                 ".gitignore", "git ls-files", "local only", "recording unavailable", "unverified"):
        assert must in v, must


def test_video_negative_never_tells_claude_to_commit_or_upload_recordings():
    for text in (SKILL.read_text(encoding="utf-8"), VIDEO.read_text(encoding="utf-8")):
        for bad in ("git add test-reports/videos", "git add -f", "--force", "upload the video"):
            assert bad not in text, bad
