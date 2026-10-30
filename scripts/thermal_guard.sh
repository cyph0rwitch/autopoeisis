#!/usr/bin/env bash
# Pause experiment processes when the GPU runs hot; stop them for good if it gets hotter.
# Usage: scripts/thermal_guard.sh LOG_FILE [PAUSE_AT] [RESUME_AT] [ABORT_AT]
# Pauses (SIGSTOP) every "python3 -m autopoiesis" process once the GPU has been at or above
# PAUSE_AT for 2 minutes, resumes (SIGCONT) at or below RESUME_AT, and at ABORT_AT kills them
# and the job queue (whose PID is read from $QUEUE_PID_FILE, if set). Logs one line per check (every 30 s).
log="$1"; pause_at="${2:-84}"; resume_at="${3:-78}"; abort_at="${4:-87}"
hot=0; paused=0
# anchored so shells whose command line merely mentions the module are never matched
procs() { pgrep -f '^(/[^ ]*/)?python3 -m autopoiesis'; }
while true; do
  read -r temp power <<< "$(nvidia-smi --query-gpu=temperature.gpu,power.draw --format=csv,noheader,nounits | tr -d ',')"
  state="running"
  if [ "$temp" -ge "$abort_at" ]; then
    [ -n "$QUEUE_PID_FILE" ] && [ -f "$QUEUE_PID_FILE" ] && kill "$(cat "$QUEUE_PID_FILE")"
    for p in $(procs); do kill -CONT "$p"; kill "$p"; done
    echo "$(date +%T) temp=${temp}C power=${power}W ABORT: stopped all experiments" >> "$log"; exit 1
  fi
  if [ "$paused" -eq 0 ]; then
    if [ "$temp" -ge "$pause_at" ]; then hot=$((hot + 1)); else hot=0; fi
    if [ "$hot" -ge 4 ]; then
      for p in $(procs); do kill -STOP "$p"; done; paused=1; state="PAUSED"
    fi
  else
    state="paused"
    if [ "$temp" -le "$resume_at" ]; then
      for p in $(procs); do kill -CONT "$p"; done; paused=0; hot=0; state="RESUMED"
    fi
  fi
  echo "$(date +%T) temp=${temp}C power=${power}W $state" >> "$log"
  sleep 30
done
