#!/usr/bin/env bash
# ============================================================
# start_all.sh — Start all UX Lens services locally
# Usage: bash start_all.sh
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "🚀 UX Lens — Starting all services"
echo "   Root: $ROOT"
echo ""

# ── Helper ───────────────────────────────────────────────────
start_python_service() {
  local name="$1"
  local dir="$2"
  local port="$3"
  local workers="${4:-2}"
  local timeout="${5:-60}"

  echo "▶  Starting $name on port $port..."

  # Create venv if missing
  if [ ! -d "$dir/.venv" ]; then
    echo "   Creating venv for $name..."
    python3 -m venv "$dir/.venv"
  fi

  source "$dir/.venv/bin/activate"

  # Install deps if requirements.txt newer than sentinel
  if [ "$dir/requirements.txt" -nt "$dir/.venv/.installed" ]; then
    echo "   Installing deps for $name..."
    pip install --quiet -r "$dir/requirements.txt"
    touch "$dir/.venv/.installed"
  fi

  # Playwright special case
  if [ "$name" = "M2:TouchTarget" ]; then
    if [ ! -f "$dir/.venv/.playwright_installed" ]; then
      echo "   Installing Playwright chromium..."
      python -m playwright install chromium
      touch "$dir/.venv/.playwright_installed"
    fi
  fi

  # Kill any old process on the port
  lsof -ti :"$port" | xargs kill -9 2>/dev/null || true

  # Start gunicorn in background
  nohup "$dir/.venv/bin/gunicorn" \
    -w "$workers" \
    -b "0.0.0.0:$port" \
    -t "$timeout" \
    --chdir "$dir" \
    app:app \
    > "/tmp/ux_$(echo $name | tr ':' '_').log" 2>&1 &

  echo "   ✅ $name started (PID $!, log: /tmp/ux_${name//:/\_}.log)"
  deactivate
}

# ── Start Python microservices ────────────────────────────────
start_python_service "M1:CognitiveLoad"  "$ROOT/services/cognitive-load"   8001  2  60
start_python_service "M2:TouchTarget"    "$ROOT/services/touch-target"     8002  1  120
start_python_service "M3:VisualHierarchy" "$ROOT/services/visual-hierarchy" 8003  1  120

# ── Wait for services to bind ─────────────────────────────────
echo ""
echo "⏳ Waiting 5s for services to bind..."
sleep 5

# ── Health checks ─────────────────────────────────────────────
echo ""
echo "🏥 Health checks:"
for port in 8001 8002 8003; do
  name=""
  case $port in
    8001) name="M1 Cognitive Load" ;;
    8002) name="M2 Touch Target" ;;
    8003) name="M3 Visual Hierarchy" ;;
  esac
  result=$(curl -s --max-time 5 "http://localhost:$port/health" 2>/dev/null || echo "FAILED")
  if echo "$result" | grep -q '"ok"'; then
    echo "   ✅ $name (port $port) — OK"
  else
    echo "   ❌ $name (port $port) — FAILED"
    echo "      → Check log: /tmp/ux_$(echo $name | tr ' ' '_').log"
  fi
done

echo ""
echo "🖥️  Express Gateway (port 5000):"
gw=$(curl -s --max-time 5 "http://localhost:5000/api/health" 2>/dev/null || echo "FAILED")
if echo "$gw" | grep -q '"ok"'; then
  echo "   ✅ Gateway — OK"
else
  echo "   ⚠️  Gateway not running. Start with:"
  echo "      cd server && npm run dev"
fi

echo ""
echo "🌐 React Client (port 3000):"
client=$(curl -s --max-time 5 "http://localhost:3000" 2>/dev/null | head -c 50 || echo "FAILED")
if [ -n "$client" ] && [ "$client" != "FAILED" ]; then
  echo "   ✅ Client — OK"
else
  echo "   ⚠️  Client not running. Start with:"
  echo "      cd client && npm run dev"
fi

echo ""
echo "════════════════════════════════════════"
echo "  Open → http://localhost:3000"
echo "════════════════════════════════════════"
