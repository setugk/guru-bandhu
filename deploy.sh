#!/bin/zsh
# Deploy Guru Bandhu's Flask backend to the NAS (clipboard/acmon-style container "guru-app", port 5055).
# scp/rsync don't work on UGOS, so files are uploaded via `ssh cat`.

NAS="Setu@10.0.0.10"
SRC="/Users/setugk/Seafile/Projects/guru-app"
REMOTE="/volume1/docker/guru-app"
SOCK="/tmp/guru-app-deploy.sock"

log() { echo "$(date '+%H:%M:%S') $1"; }

log "Connecting to NAS..."
ssh -M -S "$SOCK" -fN "$NAS" || { log "SSH connection failed"; exit 1; }

run() { ssh -S "$SOCK" "$NAS" "$1"; }
upload() {
  ssh -S "$SOCK" "$NAS" "cat > $1" < "$2" && log "  uploaded: $(basename $1)"
}

log "Preparing remote directories..."
run "mkdir -p $REMOTE/templates $REMOTE/static $REMOTE/data"

log "Uploading source files..."
upload "$REMOTE/app.py"                    "$SRC/app.py"
upload "$REMOTE/db.py"                     "$SRC/db.py"
upload "$REMOTE/create_account.py"         "$SRC/create_account.py"
upload "$REMOTE/Dockerfile"                "$SRC/Dockerfile"
upload "$REMOTE/docker-compose.yml"        "$SRC/docker-compose.yml"
upload "$REMOTE/.env"                      "$SRC/.env"
upload "$REMOTE/templates/index.html"      "$SRC/templates/index.html"
upload "$REMOTE/static/manifest.json"      "$SRC/static/manifest.json"
upload "$REMOTE/static/icon-192.png"       "$SRC/static/icon-192.png"
upload "$REMOTE/static/icon-512.png"       "$SRC/static/icon-512.png"

ssh -S "$SOCK" -O exit "$NAS" 2>/dev/null

log "Building and starting container (will prompt for the NAS sudo password)..."
ssh -t "$NAS" "cd $REMOTE && sudo docker compose up -d --build"

log "Done. Guru Bandhu → http://10.0.0.10:5055"
