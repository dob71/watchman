#!/bin/bash
# This script starts all the Watchman services locally. It's using multilog
# from daemontools (sudo apt install daemontools for Ubuntu).
# 1. Set up your and activate the virtual environment (the requirements.txt 
#    file in the project root folder lists all the packages installed in the
#    virtual environment used for the system development).
# 2. Check out the llm folder, install OLLAMA and load the model you are planning
#    to use (currently llama3.2-vision:11b-instruct-fp16, see
#    orchestrator/model_interfaces.py for details)
# 3. Create ./.env file in the project root folder. See readme files for
#    the individual subsytems for the required system configuration values.
# 4. Set up your voice control environment (Alexa or just the alerting system),
#    see ./readme_vcs.txt for details.
# 5. Start the Watchman services by executing this script (from the project's
#    root folder).
# 6. Open the UI by pointing the browser to http://localhost:8000/ and
#    configure the system's input video feeds and objects of interest.
#    Confirm the system is working. For troubleshooting check logs located
#    in the LOGS_DIR per your .env settings (by default stored in "logs"
#    folder uder DATA_DIR).

[ ! -e ./.env ] && echo "Missing ./.env file!" && exit 1

. ./.env
export LOGS_DIR="${LOGS_DIR:-${DATA_DIR}/logs}"
export UI_PORT="${UI_PORT:-8000}"

if [ "${DATA_DIR}" == "" ]; then
  echo "The DATA_DIR cannot be empty, please set up DATA_DIR in your .env file!"
  exit 1
fi

if [ ! -e "${DATA_DIR}" ]; then
  echo "The DATA_DIR \"${DATA_DIR}\" does not exist, creating..."
  ! mkdir -p "${DATA_DIR}" && echo "Unable to create \"${DATA_DIR}\", exiting!" && exit 2
fi

if [ ! -e "${IPC_DIR}" ]; then
  echo "The IPC_DIR \"${IPC_DIR}\" does not exist, creating..."
  ! mkdir -p "${IPC_DIR}" && echo "Unable to create \"${IPC_DIR}\", exiting!" && exit 2
fi

mkdir -p "$LOGS_DIR"

# export all the evironment to subshells
for var in $(env | cut -d= -f1); do
  export "$var"
done

# start all services in their own groups
( setsid $SHELL --norc --noprofile -c "echo \$\$ > $LOGS_DIR/imager.pid; while true; do python -u imager/imager.py; sleep 5; done" 2>&1 | multilog t n3 s1000000 "$LOGS_DIR/imager" & )
( setsid $SHELL --norc --noprofile -c "echo \$\$ > $LOGS_DIR/orchestrator.pid; while true; do python -u orchestrator/orchestrator.py; sleep 5; done" 2>&1 | multilog t n3 s1000000 "$LOGS_DIR/orchestrator" & )
( setsid $SHELL --norc --noprofile -c "echo \$\$ > $LOGS_DIR/announcer.pid; while true; do python -u vcs/announcer.py; sleep 5; done" 2>&1 | multilog t n3 s1000000 "$LOGS_DIR/announcer" & )
( setsid $SHELL --norc --noprofile -c "echo \$\$ > $LOGS_DIR/responder.pid; while true; do python -u vcs/responder.py; sleep 5; done" 2>&1 | multilog t n3 s1000000 "$LOGS_DIR/responder" &)
( setsid $SHELL --norc --noprofile -c "echo \$\$ > $LOGS_DIR/ui.pid; while true; do streamlit run ui/main.py --server.port $UI_PORT --server.headless true; sleep 5; done" 2>&1 | multilog t n3 s1000000 "$LOGS_DIR/ui" & )

echo "Started, see the logs in $LOGS_DIR for results."
echo "Configuration UI is at http://localhost:$UI_PORT/"
echo "Press Enter to terminate all services..."
read

source ./kill_local.sh
