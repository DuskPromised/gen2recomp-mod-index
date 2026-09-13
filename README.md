# Gen 2 Recomp Mod Index

Comprehensive GenRecomp-compatible index for **FAFF0x/gen2recomp** mods, dependencies, optional integrations, conflicts, and author-hosted downloads.

## What this repository does

- Indexes every ZIP published in `FAFF0x/gen2recomp`.
- Reads each ZIP's own `manifest.json` so IDs, versions, required dependencies, optional dependencies, conflicts, engine ranges, permissions, and descriptions come from the mod package itself.
- Keeps required dependencies separate from optional integrations.
- Adds referenced external dependencies from the wider GenRecomp ecosystem when they are needed by the FAFF0x collection.
- Shows the exact ZIP filename and direct author-hosted download link in the Pages catalog.
- Stores **no ROMs and no mirrored mod ZIP binaries**.

## Automatic updates

A scheduled GitHub Action runs daily. It re-reads the current FAFF0x repository, regenerates the feed, validates it, and commits the result only when something changed. Any verified change then triggers a GitHub Pages redeploy.

## Import URLs

After Pages is enabled:

- Repository slug: `DuskPromised/gen2recomp-mod-index`
- Feed: `https://duskpromised.github.io/gen2recomp-mod-index/data/index.json`
- Catalog: `https://duskpromised.github.io/gen2recomp-mod-index/`

Source collection: https://github.com/FAFF0x/gen2recomp
