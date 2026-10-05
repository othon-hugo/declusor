_FIND_PRINTF_PATTERN='%-12M %u:%-10g %p\n'

_err() {
    printf '%s: %s\n' "${FUNCNAME[1]:-std}" "$*" >&2;
}

_have() {
    command -v "$1" >/dev/null 2>&1;
}

encode_b64() {
    { [ $# -gt 0 ] && printf '%s' "$1" || cat; } | {
        if command -v base64 >/dev/null 2>&1; then
            base64 | tr -d '\r\n'
        elif command -v openssl >/dev/null 2>&1; then
            openssl base64 -A
        elif command -v python3 >/dev/null 2>&1; then
            python3 -c 'import sys, base64; sys.stdout.write(base64.b64encode(sys.stdin.buffer.read()).decode("ascii"))'
        elif command -v perl >/dev/null 2>&1; then
            perl -MMIME::Base64 -0777 -ne 'print encode_base64($_, "")'
        fi
    }

    printf '\n'
}

decode_b64() {
    { [ $# -gt 0 ] && printf '%s' "$1" || cat; } | {
        if command -v base64 >/dev/null 2>&1; then
            base64 -d 2>/dev/null || base64 -D 2>/dev/null
        elif command -v openssl >/dev/null 2>&1; then
            openssl enc -d -base64 -A 2>/dev/null
        elif command -v python3 >/dev/null 2>&1; then
            python3 -c 'import sys, base64; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read()))' 2>/dev/null
        elif command -v perl >/dev/null 2>&1; then
            perl -MMIME::Base64 -0777 -ne 'print decode_base64($_)' 2>/dev/null
        fi
    }
}

hash_value() {
    local algo="sha256"

    while [ $# -gt 0 ]; do
        case "$1" in
            -a) algo="$2"; shift 2 ;;
            *) break ;;
        esac
    done

    { [ $# -gt 0 ] && printf '%s' "$1" || cat; } | {
        if command -v "${algo}sum" >/dev/null 2>&1; then
            "${algo}sum" | awk '{print $1}'
        elif command -v shasum >/dev/null 2>&1; then
            shasum -a "${algo#sha}" 2>/dev/null | awk '{print $1}'
        elif command -v openssl >/dev/null 2>&1; then
            openssl dgst "-$algo" 2>/dev/null | awk '{print $NF}'
        elif [ "$algo" = "md5" ] && command -v md5 >/dev/null 2>&1; then
            md5 -q
        fi
    }
}

store_file() {
    local target="$1"

    if [ -z "$target" ]; then
        local target_dir

        for dir in /dev/shm /tmp /var/tmp "${TMPDIR:-/tmp}" .; do
            if [ -d "$dir" ] && [ -w "$dir" ]; then
                target_dir="$dir"
                break
            fi
        done

        target_dir="${target_dir:-/tmp}"
        target="$(mktemp "$target_dir/declusor.XXXXXX" 2>/dev/null || echo "$target_dir/declusor_$$.temp")"
    fi

    cat > "$target" && printf '%s\n' "$target"
}

remove_file() {
    [ -n "$1" ] && rm -f -- "$1" 2>/dev/null
}

execute_source() {
    local code

    if [ $# -gt 0 ]; then
        code="$1"
        shift
    else
        code="$(cat)"
    fi

    eval "$code"
}

execute_binary() {
    local cleanup=0

    if [ "$1" = "--cleanup" ]; then
        cleanup=1
        shift
    fi

    local filepath="$1"
    shift

    [ -f "$filepath" ] || { printf 'file not found: %s\n' "$filepath" >&2; return 1; }

    chmod +x "$filepath" 2>/dev/null

    "$filepath" "$@"
    local rc=$?

    [ $cleanup -eq 1 ] && rm -f -- "$filepath" 2>/dev/null

    return $rc
}

list_perms() {
    local target="${1:-.}"

    if find . -prune -printf '' >/dev/null 2>&1; then
        find "$target" -maxdepth 1 -printf "$_FIND_PRINTF_PATTERN" 2>/dev/null
    elif command -v stat >/dev/null 2>&1; then
        stat -c '%A %U:%G %n' "$target"/* 2>/dev/null || stat -f '%Sp %Su:%Sg %N' "$target"/* 2>/dev/null
    else
        ls -ld "$target"/* 2>/dev/null | awk '{print $1, $3":"$4, $9}'
    fi
}

_column_fallback() {
    local sep=" "

    while [ $# -gt 0 ]; do
        case "$1" in
            -s) sep="$2"; shift 2 ;;
            -s*) sep="${1#-s}"; shift ;;
            -t) shift ;;
            *) shift ;;
        esac
    done

    awk -F"$sep" '{
        for (i=1; i<=NF; i++) {
            if (length($i) > w[i]) w[i] = length($i)
            row[NR, i] = $i
        }
        if (NF > cols) cols = NF
        rows = NR
    }
    END {
        for (r=1; r<=rows; r++) {
            for (c=1; c<=cols; c++) {
                if (c < cols) printf "%-*s  ", w[c], row[r, c]
                else printf "%s", row[r, c]
            }
            printf "\n"
        }
    }'
}

_have column || column() { _column_fallback "$@"; }

label() {
    local title=$1 printed=0 line

    while IFS= read -r line || [ -n "$line" ]; do
        if [ "$printed" -eq 0 ]; then
            printf '\n%s\n' "$(printf '%s' "$title" | tr '[:lower:]' '[:upper:]')"
            printf '%*s\n' "${#title}" '' | tr ' ' '-'
            printed=1
        fi

        printf '%s\n' "$line"
    done
}
