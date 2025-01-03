#!/bin/bash
# Kill the services started by start_local.sh

[ ! -e ./.env ] && echo "Missing ./.env file!" && exit 1

. ./.env
export LOGS_DIR="${LOGS_DIR:-${DATA_DIR}/logs}"
export UI_PORT="${UI_PORT:-8000}"

PID_LIST="$(cat $LOGS_DIR/imager.pid) $(cat $LOGS_DIR/orchestrator.pid) $(cat $LOGS_DIR/announcer.pid) $(cat $LOGS_DIR/responder.pid) $(cat $LOGS_DIR/ui.pid)"

echo "Killing groups $PID_LIST ..."
for pid in $PID_LIST; do
    kill -- -$pid  1>/dev/null 2>&1
done
echo "Waiting 10sec..."
sleep 5
# another run before SIGKILL
for pid in $PID_LIST; do
    kill -- -$pid  1>/dev/null 2>&1
done
sleep 5
echo "Checking if still running..."
for pid in $PID_LIST; do
    if ! pgrep -g $pid; then
        echo "Group $pid terminated"
    else
        echo "Group $pid still has running processes, sending SIGKILL"
        kill -9 -- -$pid  1>/dev/null 2>&1
    fi
done
echo "Done"
