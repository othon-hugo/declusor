useful_tools=(nc netcat ncat telnet socat gcc nmap wget curl tcpdump ftp)

# list useful tools
( for tool in "${useful_tools[@]}"; do which "$tool"; done ) 2> /dev/null | label 'Development Tools'
