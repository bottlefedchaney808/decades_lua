#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"; mkdir -p "$ROOT/.run"
for p in 8732 8731; do
  if ss -ltn "sport = :$p" | grep -q LISTEN; then echo "port $p already busy — not stealing it"; exit 1; fi
done
/usr/bin/python3 "$ROOT/.publish/wow4_sims/upstream-classic/tools/forever_gen/serve_dist.py" 8732 >"$ROOT/.run/sim.log" 2>&1 &
echo $! > "$ROOT/.run/sim.pid"
/usr/bin/python3 "$ROOT/wow-forever/serve_tiles.py" --host 0.0.0.0 --port 8731 >"$ROOT/.run/map.log" 2>&1 &
echo $! > "$ROOT/.run/map.pid"
for i in $(seq 1 10); do
  ss -ltn 'sport = :8732' | grep -q LISTEN && ss -ltn 'sport = :8731' | grep -q LISTEN && break
  sleep 0.5
done
ss -ltn 'sport = :8732' | grep -q LISTEN && ss -ltn 'sport = :8731' | grep -q LISTEN || { echo "a service failed to bind — see .run/*.log"; exit 1; }
# LAN IP = the source address of the default route: bond0 can carry several
# global IPs (LAN + hotspot 192.168.137.x); hostname -I picks them in any
# order, and the hotspot one is unreachable from real-LAN clients.
LANIP="$(ip route 2>/dev/null | awk '/^default / {for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"
[ -n "$LANIP" ] && ip -4 -o addr show scope global | grep -q " $LANIP/" || LANIP="$(hostname -I | awk '{print $1}')"
echo "sim: http://$LANIP:8732/forever/   map: http://$LANIP:8731/"
