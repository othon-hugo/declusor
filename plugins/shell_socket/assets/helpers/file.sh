function hash_value() {
    if [ "$1" ]; then
        if [ -x "$(command -v sha256sum)" ]; then
            echo "$1" | sha256sum | head -c 64
        elif [ -x "$(command -v sha384sum)" ]; then
            echo "$1" | sha384sum | head -c 96
        elif [ -x "$(command -v sha512sum)" ]; then
            echo "$1" | sha512sum | head -c 124
        elif [ -x "$(command -v sha1sum)" ]; then
            echo "$1" | sha1sum | head -c 40
        elif [ -x "$(command -v md5sum)" ]; then
            echo "$1" | md5sum | head -c 32
        else
            >&2 echo "can't hash data"
        fi
    else
        >&2 echo "data not found"
    fi
}

function store_base64_encoded_value() {
    if [ "$1" ]; then
        datahash=$(hash_value "$1" 2> /dev/null)

        if [ "$datahash" ]; then
            filepath="/tmp/$datahash.temp"
        else
            filepath="/tmp/custom-file.temp"
        fi
        
        (echo -n "$1" | base64 -d) > "$filepath" && echo "$filepath" || >&2 echo "cannot decode data"
    else
        >&2 echo "data not found"
    fi
}

function execute_base64_encoded_value() {
    if [ "$1" ]; then
        filepath=$(store_base64_encoded_value "$1" 2> /dev/null)

        shift

        if [ "$filepath" ]; then
            chmod 700 "$filepath" && "$filepath" "$@"
            rm "$filepath"
        else
            >&2 echo "file doesn't exist"
        fi
    else
        >&2 echo "data not found"
    fi
}