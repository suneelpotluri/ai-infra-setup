# =============================================================================
# WSL2 Setup Script for AI Infrastructure System
# Run in PowerShell as Administrator
# =============================================================================

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " WSL2 Setup for AI Infrastructure System" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# ─── Step 1: Install WSL2 ────────────────────────────────────────────────────
Write-Host "`n[1/5] Installing WSL2 with Ubuntu 22.04..." -ForegroundColor Yellow
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
Write-Host "✅ WSL2 installed — REBOOT REQUIRED before continuing" -ForegroundColor Green
Write-Host "After reboot, run this script again from Step 2" -ForegroundColor Yellow

# ─── Step 2: Move WSL2 to F: drive ───────────────────────────────────────────
Write-Host "`n[2/5] Moving WSL2 to F: drive..." -ForegroundColor Yellow

# Terminate running instances
wsl --terminate Ubuntu-22.04

# Create directory structure on F:
if (-not (Test-Path "F:\WSL")) { New-Item -ItemType Directory -Path "F:\WSL" }
if (-not (Test-Path "F:\WSL\Ubuntu2204")) { New-Item -ItemType Directory -Path "F:\WSL\Ubuntu2204" }

# Export
Write-Host "Exporting Ubuntu-22.04 (this takes 5-10 mins)..." -ForegroundColor Yellow
wsl --export Ubuntu-22.04 "F:\WSL\ubuntu2204.tar"

# Unregister from C: drive
wsl --unregister Ubuntu-22.04

# Import to F: drive
Write-Host "Importing to F: drive (this takes 5-10 mins)..." -ForegroundColor Yellow
wsl --import Ubuntu-22.04 "F:\WSL\Ubuntu2204" "F:\WSL\ubuntu2204.tar"

Write-Host "✅ WSL2 moved to F: drive" -ForegroundColor Green

# ─── Step 3: Set default user ────────────────────────────────────────────────
Write-Host "`n[3/5] Setting default user to sunilp..." -ForegroundColor Yellow
wsl -d Ubuntu-22.04 -u root bash -c "echo -e '[user]\ndefault=sunilp' >> /etc/wsl.conf"
wsl --terminate Ubuntu-22.04
Write-Host "✅ Default user set" -ForegroundColor Green

# ─── Step 4: Verify ──────────────────────────────────────────────────────────
Write-Host "`n[4/5] Verifying setup..." -ForegroundColor Yellow
wsl --list --verbose
Write-Host "✅ WSL2 distros listed above" -ForegroundColor Green

# ─── Step 5: Cleanup ─────────────────────────────────────────────────────────
Write-Host "`n[5/5] Cleaning up tar file (saves ~18GB on F:)..." -ForegroundColor Yellow
$confirm = Read-Host "Delete F:\WSL\ubuntu2204.tar? (y/n)"
if ($confirm -eq 'y') {
    Remove-Item "F:\WSL\ubuntu2204.tar" -Force
    Write-Host "✅ Tar file deleted" -ForegroundColor Green
} else {
    Write-Host "⚠️  Tar file kept as backup at F:\WSL\ubuntu2204.tar" -ForegroundColor Yellow
}

# ─── Summary ─────────────────────────────────────────────────────────────────
Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host " WSL2 Setup Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Launch Ubuntu WSL2:" -ForegroundColor White
Write-Host "  wsl -d Ubuntu-22.04" -ForegroundColor Gray
Write-Host ""
Write-Host "Next step: Run phase1-central-ai/setup.sh inside WSL2" -ForegroundColor Yellow
