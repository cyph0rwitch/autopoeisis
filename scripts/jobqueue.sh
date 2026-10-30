#!/usr/bin/env bash
# Run experiment commands from a jobs file one at a time; lines can be appended while it runs.
# Usage: scripts/jobqueue.sh JOBS_FILE LOG_FILE
# A line is marked done by appending its number to JOBS_FILE.done. A file named STOP next
# to JOBS_FILE ends the queue after the current job.
jobs="$1"; log="$2"; done_file="$jobs.done"; touch "$done_file"
echo $$ > "$jobs.pid"
cd "$(dirname "$0")/.."
while true; do
  [ -e "$(dirname "$jobs")/STOP" ] && { echo "STOP file found $(date +%T)" >> "$log"; exit 0; }
  n=0; next=""
  while IFS= read -r line; do
    n=$((n + 1))
    [[ -z "$line" || "$line" == \#* ]] && continue
    grep -qx "$n" "$done_file" || { next="$line"; break; }
  done < "$jobs"
  if [ -z "$next" ]; then echo "QUEUE EMPTY $(date +%T)" >> "$log"; exit 0; fi
  echo "=== job $n $(date +%T): $next" >> "$log"
  bash -c "$next" > /dev/null 2>&1 || echo "FAILED job $n" >> "$log"
  echo "$n" >> "$done_file"
done
