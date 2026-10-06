# show current UID and GID
( id ) | label "Current User/Group"

# show current user's sudo nopasswd permissions
( sudo -n -l | grep 'NOPASSWD' | awk '{$1=$1;print}' ) 2> /dev/null | label "Sudo NOPASSWD Permission"

# show last logged in users
( lastlog | grep -vE '\*\*.*\*\*' | cut -d $'\n' -f 2- ) | tail -n +2 | column -t 2> /dev/null | label "Last Logged In Users"

# show all users logged into the current system
( w -hs ) 2> /dev/null | label "Users Logged In"

# list all user accounts
( while IFS= read -r uid; do id "$uid"; done < <(awk -F ':' '{ print $1 }' /etc/passwd) ) 2> /dev/null | column -t | label "Current Users"

# list all super user accounts
( while IFS= read -r uid; do id "$uid"; done < <(grep -Po '^sudo.+:\K.*$' /etc/group) ) 2> /dev/null | label "Super Users"

# list all adm accounts
( while IFS= read -r uid; do id "$uid"; done < <(grep -Po '^adm.+:\K.*$' /etc/group) ) 2> /dev/null | label "ADM Users"
