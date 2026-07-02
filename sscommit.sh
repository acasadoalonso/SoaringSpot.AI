#!/bin/bash
scp -r aiserver:.claude/skills/check-club-handicaps/ skills/
scp -r aiserver:.claude/skills/download-igc/ skills/
scp -r aiserver:formulas/ formulas/
git add .
git commit
