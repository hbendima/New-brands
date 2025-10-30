#!/bin/sh
set -e

BRANCH="normalize-structure"

# Zorg dat we up-to-date zijn
git fetch origin

# Maak en wissel naar feature branch
git checkout -b "$BRANCH"

# Maak de gewenste mappen
mkdir -p scripts docs

# Verplaats en hernoem bestanden (stil blijven als een bronbestand niet bestaat)
git mv -v scripts_build_Version5.py scripts/build.py || echo "scripts_build_Version5.py niet gevonden, overslaan"
git mv -v docs_index_Version5.html docs/index.html || echo "docs_index_Version5.html niet gevonden, overslaan"
git mv -v requirements_Version5.txt requirements.txt || echo "requirements_Version5.txt niet gevonden, overslaan"
git mv -v env_Version6.example .env.example || echo "env_Version6.example niet gevonden, overslaan"
git mv -v gitignore_Version4 .gitignore || echo "gitignore_Version4 niet gevonden, overslaan"

# Stage en commit (als er wijzigingen zijn)
git add -A
if git diff --cached --quiet; then
  echo "Geen wijzigingen om te committen."
else
  git commit -m "Normalize repo structure: move scripts/ and docs/, standard filenames"
fi

# Push de nieuwe branch
git push -u origin "$BRANCH"

echo "Klaar. Branch gepusht: $BRANCH. Maak een PR vanaf deze branch naar main."