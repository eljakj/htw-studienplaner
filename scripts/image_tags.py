#!/usr/bin/env python3
"""Tags for the container image, used by .github/workflows/release-image.yml.

    python scripts/image_tags.py ghcr.io/owner/name <commit-sha> --main
    python scripts/image_tags.py ghcr.io/owner/name <commit-sha> --tag v1.2.3

Prints one image reference per line.

    every build   <image>:sha-<7 characters of the commit>
    --main        <image>:latest             (build of a commit on main)
    --tag v1.2.3  <image>:1.2.3, :1.2, :1    (:1 only from version 1.0.0 on)
    --tag v1.2.3-rc.1                        only <image>:1.2.3-rc.1 (pre-release)
"""
import argparse
import re
import sys

SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def image_tags(image, sha, main=False, tag=None):
    if image != image.lower():
        raise ValueError("image name must be lowercase: %r" % image)
    if not SHA.match(sha):
        raise ValueError("not a full commit sha: %r" % sha)

    tags = ["%s:sha-%s" % (image, sha[:7])]
    if main:
        tags.append("%s:latest" % image)
    if tag:
        m = SEMVER.match(tag)
        if not m:
            raise ValueError("tag %r is not a version like v1.2.3" % tag)
        major, minor, patch, pre = m.groups()
        tags.append("%s:%s.%s.%s%s" % (image, major, minor, patch, pre or ""))
        if not pre:
            tags.append("%s:%s.%s" % (image, major, minor))
            if major != "0":
                tags.append("%s:%s" % (image, major))
    return tags


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("sha")
    ap.add_argument("--main", action="store_true", help="the commit is on main")
    ap.add_argument("--tag", help="git tag like v1.2.3")
    args = ap.parse_args(argv)
    try:
        tags = image_tags(args.image, args.sha, args.main, args.tag)
    except ValueError as error:
        sys.exit("error: %s" % error)
    print("\n".join(tags))


if __name__ == "__main__":
    main()
