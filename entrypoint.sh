#!/bin/bash
set -e

# Render (and most PaaS) set PORT env var for the app to listen on.
# We need nginx to listen on $PORT, while keeping backend on internal port 8000.
LISTEN_PORT="${PORT:-80}"
BACKEND_PORT="8000"

echo "=== SYNTHESIA Entrypoint ==="
echo "  External port (nginx): $LISTEN_PORT"
echo "  Internal port (backend): $BACKEND_PORT"

# Update nginx to listen on the correct port
sed -i "s/listen 80;/listen ${LISTEN_PORT};/" /etc/nginx/conf.d/default.conf

# Ensure backend always runs on internal port 8000 (not the external PORT)
export PORT=$BACKEND_PORT

echo "  Nginx config updated, starting services..."

# Start supervisor (runs both nginx and backend)
exec supervisord -c /etc/supervisor/conf.d/synthesia.conf
