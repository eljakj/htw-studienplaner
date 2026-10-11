"""Tests for scripts/image_tags.py."""
import pytest

import image_tags

IMAGE = "ghcr.io/eljakj/htw-studienplaner"
SHA = "0123456789abcdef0123456789abcdef01234567"


def test_main_build_gets_sha_and_latest():
    assert image_tags.image_tags(IMAGE, SHA, main=True) == [IMAGE + ":sha-0123456", IMAGE + ":latest"]


def test_every_build_gets_the_short_sha_tag():
    assert image_tags.image_tags(IMAGE, SHA) == [IMAGE + ":sha-0123456"]


def test_release_tag_gets_semver_tags():
    assert image_tags.image_tags(IMAGE, SHA, tag="v1.2.3") == [
        IMAGE + ":sha-0123456",
        IMAGE + ":1.2.3",
        IMAGE + ":1.2",
        IMAGE + ":1",
    ]


def test_version_zero_has_no_major_tag():
    tags = image_tags.image_tags(IMAGE, SHA, tag="v0.3.1")
    assert IMAGE + ":0.3" in tags
    assert IMAGE + ":0" not in tags


def test_prerelease_gets_only_its_own_tag():
    assert image_tags.image_tags(IMAGE, SHA, tag="v1.2.3-rc.1") == [
        IMAGE + ":sha-0123456",
        IMAGE + ":1.2.3-rc.1",
    ]


@pytest.mark.parametrize("tag", ["1.2.3", "v1.2", "vnext", "v1.2.3;rm"])
def test_bad_tag_is_rejected(tag):
    with pytest.raises(ValueError):
        image_tags.image_tags(IMAGE, SHA, tag=tag)


def test_uppercase_image_and_short_sha_are_rejected():
    with pytest.raises(ValueError):
        image_tags.image_tags("ghcr.io/ELJAKJ/x", SHA)
    with pytest.raises(ValueError):
        image_tags.image_tags(IMAGE, "0123456")


def test_command_line_prints_one_tag_per_line(capsys):
    image_tags.main([IMAGE, SHA, "--main"])
    assert capsys.readouterr().out.splitlines() == [IMAGE + ":sha-0123456", IMAGE + ":latest"]
