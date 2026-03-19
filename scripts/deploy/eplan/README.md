# ePlan Import Tool -- Deploy

## Bouwen

```
cd scripts/
python -m PyInstaller --clean eplan-import-tool.spec
```

Output: `scripts/dist/eplan-import-tool.exe`

## Installeren op test share (Y:)

```
PowerShell -ExecutionPolicy Bypass -File scripts/deploy/eplan/install-test.ps1
```

## Installeren op live share (Z:)

```
PowerShell -ExecutionPolicy Bypass -File scripts/deploy/eplan/install-live.ps1
```

## GitHub release aanmaken

```
gh release create eplan-v1.0.0 "scripts/dist/eplan-import-tool.exe" \
  --repo ritco/spinnekop-tools \
  --title "ePlan Import Tool v1.0.0" \
  --notes "Eerste release"
```

Zie `workflows/tool-release-pipeline.md` voor volledig draaiboek.
