#! /usr/bin/env bash
# =============================================================================
# Copyright [2013] [Kevin Carter]
# License Information :
# This software has no warranty, it is provided 'as is'. It is your
# responsibility to validate the behavior of the routines and its accuracy
# using the code provided. Consult the GNU General Public license for further
# details (see GNU General Public License).
# http://www.gnu.org/licenses/gpl.html
# =============================================================================

### BEGIN INIT INFO
# Provides:          eventlet_wsgi
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Should-Start:      $named
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: WSGI Server
# Description:       WSGI Server
### END INIT INFO

set -e

export PATH="${PATH:+$PATH:}/usr/sbin:/sbin"

# /etc/init.d/eventlet_wsgi: start and stop the eventlet_wsgi daemon
# Change the PROGRAM_NAME variable to what ever suits your application.
# Normally PROGRAM_NAME would be the binary to start your application.
PROGRAM_NAME="eventlet_wsgi"

DAEMON="${PROGRAM_NAME}"
CONFIG_FILE="/etc/eventlet_wsgi/eventlet_wsgi.conf"
PID_FILE="/var/run/${PROGRAM_NAME}.pid"

source /lib/lsb/init-functions

app_api_start() {
    if [ ! -s "$CONFIG_FILE" ]; then
        log_failure_msg "missing or empty config file $CONFIG_FILE"
        log_end_msg 1
        exit 0
    fi
        if start-stop-daemon --start --quiet --background \
        --pidfile $PID_FILE --make-pidfile --exec $DAEMON \
        -- --config-file ${CONFIG_FILE}
    then
        rc=0
        sleep 1
        if ! kill -0 $(cat $PID_FILE) >/dev/null 2>&1; then
            rc=1
        fi
    else
        rc=1
    fi

    if [ $rc -eq 0 ]; then
        log_end_msg 0
    else
        log_failure_msg "${PROGRAM_NAME} daemon failed to start"
        log_end_msg 1
        rm -f $PID_FILE
    fi
}


case "$1" in
  start)
        log_daemon_msg "Starting ${PROGRAM_NAME} daemon" "${PROGRAM_NAME}"
        if [ -s $PID_FILE ] && kill -0 $(cat $PID_FILE) >/dev/null 2>&1; then
            log_progress_msg "${PROGRAM_NAME} is already running"
            log_end_msg 0
            exit 0
        fi
        app_api_start
        ;;
  stop)
        log_daemon_msg "Stopping ${PROGRAM_NAME} daemon" "${PROGRAM_NAME}"
        start-stop-daemon --stop --quiet --oknodo --pidfile $PID_FILE
        log_end_msg $?
        rm -f $PID_FILE
        ;;
  restart)
        set +e
        log_daemon_msg "Restarting ${PROGRAM_NAME} daemon" "${PROGRAM_NAME}"
        if [ -s $PID_FILE ] && kill -0 $(cat $PID_FILE) >/dev/null 2>&1; then
            start-stop-daemon --stop --quiet --oknodo --pidfile $PID_FILE || true
            sleep 1
        else
            log_warning_msg "${PROGRAM_NAME} daemon not running, attempting to start."
            rm -f $PID_FILE
        fi
        app_api_start
        ;;

  status)
        status_of_proc -p $PID_FILE "$(which $DAEMON)" ${PROGRAM_NAME}
        exit $?
        ;;
  *)
        echo "Usage: /etc/init.d/${PROGRAM_NAME} {start|stop|restart|status}"
        exit 1
esac

exit 0
