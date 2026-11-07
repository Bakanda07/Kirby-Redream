# About this fork

This is a fork of [josiahg2502-glitch/Kirby-Redream](https://github.com/josiahg2502-glitch/Kirby-Redream), maintained by Bakanda07 as a continuation of the open-source project. It carries the upstream work as it stood on the date below.

- Game / target: Kirby and the Forgotten Land (Switch, AArch64)
- Licence: GPL-3.0. The licence file and the author notices of the upstream repository are kept as they are.
- Base commit: `95387a1961a13df79e50a85e1bee4b8606b5bd3c` (95387a1, 2026-11-06: "Pin the runtime package of this version")
- Base tag: `upstream-base-2026-11-07` marks that commit in this repository.
- Default branch: `main`

## What differs from upstream

None. `main` is identical to upstream at the base commit.

## Releases and mirrors

Releases v1.0.0 and `installer-tools` are mirrored on this account. Branch `mirror-bakanda07` (1 commit) repoints the installer, updater (`runtime/updater.c`) and download scripts to this account; it is not merged into `main` yet.

Releases published here before any change of ours are copies of the upstream builds. They are not built from this repository.

## Following upstream

```sh
git fetch upstream
git log --oneline main..upstream/main
git merge --ff-only upstream/main
```

## Rules for this fork

- No game data, keys, extracted files or code generated from a game goes into this repository.
- A release built from this fork must say so in its name or notes and give the base tag it started from.
- Changes of ours are listed in the section above when they are merged.
