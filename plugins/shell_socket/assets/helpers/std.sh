# -----------------------------------------------------------------------------
# Standard Runtime Helper Library for Remote Shell Sessions
#
# Provides an Anti-Corruption Layer (ACL) of portable, multi-fallback
# primitives for encoding, compression, hashing, archiving, storage,
# execution, network probing, system inspection, and presentation.
# All errors are captured and filtered locally on the target.
# -----------------------------------------------------------------------------

_FIND_PRINTF_PATTERN='%-12M %u:%-10g %p\n'

# =============================================================================
# Internal Diagnostics & Capability Discovery
# =============================================================================

# Silently swallow internal helper errors so nothing leaks to the operator
_err() {
    return 0
}

# Check if a command or binary is available in the current environment
_have() {
    command -v "$1" >/dev/null 2>&1
}

# =============================================================================
# Encoding & Cryptographic Hashing
# =============================================================================

# Encode input data or piped stream into an ASCII Base64 string
encode_b64() {
    {
        if [ $# -gt 0 ]; then
            printf '%s' "$1"
        else
            cat
        fi
    } 2>/dev/null | {
        if _have base64; then
            base64 2>/dev/null | tr -d '\r\n'
        elif _have openssl; then
            openssl base64 -A 2>/dev/null
        elif _have python3; then
            python3 -c 'import sys, base64; sys.stdout.write(base64.b64encode(sys.stdin.buffer.read()).decode("ascii"))' 2>/dev/null
        elif _have perl; then
            perl -MMIME::Base64 -0777 -ne 'print encode_base64($_, "")' 2>/dev/null
        fi
    }

    printf '\n'
}

# Decode Base64 input or piped stream into raw bytes
decode_b64() {
    {
        if [ $# -gt 0 ]; then
            printf '%s' "$1"
        else
            cat
        fi
    } 2>/dev/null | {
        if _have base64; then
            base64 -d 2>/dev/null || base64 -D 2>/dev/null
        elif _have openssl; then
            openssl enc -d -base64 -A 2>/dev/null
        elif _have python3; then
            python3 -c 'import sys, base64; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read()))' 2>/dev/null
        elif _have perl; then
            perl -MMIME::Base64 -0777 -ne 'print decode_base64($_)' 2>/dev/null
        fi
    }
}

# Calculate cryptographic digest of input data or stream
hash_value() {
    local algo="sha256"

    while [ $# -gt 0 ]; do
        case "$1" in
            -a) algo="$2"; shift 2 ;;
            *) break ;;
        esac
    done

    {
        if [ $# -gt 0 ]; then
            printf '%s' "$1"
        else
            cat
        fi
    } 2>/dev/null | {
        if _have "${algo}sum"; then
            "${algo}sum" 2>/dev/null | awk '{print $1}'
        elif _have shasum; then
            shasum -a "${algo#sha}" 2>/dev/null | awk '{print $1}'
        elif _have openssl; then
            openssl dgst "-$algo" 2>/dev/null | awk '{print $NF}'
        elif _have python3; then
            python3 -c "import sys, hashlib; print(hashlib.new('$algo', sys.stdin.buffer.read()).hexdigest())" 2>/dev/null
        elif [ "$algo" = "md5" ] && _have md5; then
            md5 -q 2>/dev/null
        fi
    }
}

# =============================================================================
# Stream Compression & Directory Archiving
# =============================================================================

# Compress input data or stream using gzip format
# shellcheck disable=SC2120
compress_gzip() {
    {
        if [ $# -gt 0 ]; then
            printf '%s' "$1"
        else
            cat
        fi
    } 2>/dev/null | {
        if _have gzip; then
            gzip -c 2>/dev/null
        elif _have python3; then
            python3 -c 'import sys, gzip; sys.stdout.buffer.write(gzip.compress(sys.stdin.buffer.read()))' 2>/dev/null
        elif _have perl; then
            perl -e 'use IO::Compress::Gzip qw(gzip); gzip "-", "-" or die;' 2>/dev/null
        fi
    }
}

# Decompress gzip-compressed input or stream
# shellcheck disable=SC2120
decompress_gzip() {
    {
        if [ $# -gt 0 ]; then
            printf '%s' "$1"
        else
            cat
        fi
    } 2>/dev/null | {
        if _have gzip; then
            gzip -dc 2>/dev/null
        elif _have python3; then
            python3 -c 'import sys, gzip; sys.stdout.buffer.write(gzip.decompress(sys.stdin.buffer.read()))' 2>/dev/null
        elif _have perl; then
            perl -e 'use IO::Uncompress::Gunzip qw(gunzip); gunzip "-", "-" or die;' 2>/dev/null
        fi
    }
}

# Package a directory into a compressed archive file or stdout stream
archive_dir() {
    local dir="$1" target="${2:-}"

    [ -d "$dir" ] || return 1

    if [ -n "$target" ]; then
        if _have tar; then
            tar -czf "$target" -C "$dir" . 2>/dev/null || { tar -cf - -C "$dir" . 2>/dev/null | compress_gzip > "$target"; }
        elif _have python3; then
            python3 -c 'import sys, tarfile; tar = tarfile.open(sys.argv[2], "w:gz"); tar.add(sys.argv[1], arcname="."); tar.close()' "$dir" "$target" 2>/dev/null
        else
            return 1
        fi
    else
        if _have tar; then
            tar -czf - -C "$dir" . 2>/dev/null || { tar -cf - -C "$dir" . 2>/dev/null | compress_gzip; }
        elif _have python3; then
            python3 -c 'import sys, io, tarfile; buf = io.BytesIO(); tar = tarfile.open(fileobj=buf, mode="w:gz"); tar.add(sys.argv[1], arcname="."); tar.close(); sys.stdout.buffer.write(buf.getvalue())' "$dir" 2>/dev/null
        else
            return 1
        fi
    fi
}

# Extract a compressed archive from a file path or piped stdin ('-') into a destination directory
extract_archive() {
    local src="$1" dest="${2:-.}"

    mkdir -p "$dest" 2>/dev/null || return 1

    if [ "$src" = "-" ]; then
        if _have tar; then
            tar -xzf - -C "$dest" 2>/dev/null || { decompress_gzip | tar -xf - -C "$dest" 2>/dev/null; }
        elif _have python3; then
            python3 -c 'import sys, io, tarfile; tar = tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()), mode="r:gz"); tar.extractall(sys.argv[1]); tar.close()' "$dest" 2>/dev/null
        else
            return 1
        fi
    else
        [ -f "$src" ] || return 1
        if _have tar; then
            tar -xzf "$src" -C "$dest" 2>/dev/null || { decompress_gzip < "$src" | tar -xf - -C "$dest" 2>/dev/null; }
        elif _have python3; then
            python3 -c 'import sys, tarfile; tar = tarfile.open(sys.argv[1], "r:gz"); tar.extractall(sys.argv[2]); tar.close()' "$src" "$dest" 2>/dev/null
        else
            return 1
        fi
    fi
}

# =============================================================================
# File Storage & Artifact Cleanup
# =============================================================================

# Resolve a writable temporary base directory on the target host
_resolve_writable_dir() {
    local dir
    for dir in /dev/shm /tmp /var/tmp "${TMPDIR:-/tmp}" .; do
        if [ -d "$dir" ] && [ -w "$dir" ]; then
            printf '%s\n' "$dir"
            return 0
        fi
    done
    printf '/tmp\n'
}

# Create an isolated ephemeral directory and output its path
mktemp_dir() {
    local base_dir target_dir
    base_dir="$(_resolve_writable_dir)"
    target_dir="$(mktemp -d "$base_dir/.declusor.XXXXXX" 2>/dev/null)"
    if [ -z "$target_dir" ] || [ ! -d "$target_dir" ]; then
        target_dir="$base_dir/.declusor_$$_$(date +%s 2>/dev/null || echo 0)"
        mkdir -p "$target_dir" 2>/dev/null || return 1
    fi
    printf '%s\n' "$target_dir"
}

# Write piped stdin data to a target file or ephemeral location and output its path
store_file() {
    local target="${1:-}"

    if [ -z "$target" ]; then
        local target_dir
        target_dir="$(_resolve_writable_dir)"
        target="$(mktemp "$target_dir/declusor.XXXXXX" 2>/dev/null || echo "$target_dir/declusor_$$.temp")"
    fi

    cat > "$target" 2>/dev/null && printf '%s\n' "$target"
}

# Silently remove a file or directory path
remove_file() {
    [ -n "$1" ] && rm -rf -- "$1" 2>/dev/null
    return 0
}

# =============================================================================
# Remote Execution & Process Invocation
# =============================================================================

# Evaluate shell source code within the current session scope
execute_source() {
    local code

    if [ $# -gt 0 ]; then
        code="$1"
        shift
    else
        code="$(cat 2>/dev/null)"
    fi

    eval "$code" 2>/dev/null
}

# Make a target binary executable, invoke it with arguments, and optionally unlink it
execute_binary() {
    local cleanup=0

    if [ "${1:-}" = "--cleanup" ]; then
        cleanup=1
        shift
    fi

    local filepath="${1:-}"
    [ -n "$filepath" ] && [ -f "$filepath" ] || return 1
    shift

    chmod +x "$filepath" 2>/dev/null

    "$filepath" "$@" 2>/dev/null
    local rc=$?

    [ $cleanup -eq 1 ] && remove_file "$filepath"

    return $rc
}

# =============================================================================
# Network Transfer & Probing Primitives
# =============================================================================

# Retrieve remote content via HTTP/HTTPS with optional method, header, and timeout flags
# Usage: fetch_url [-X METHOD] [-H HEADER] [-t TIMEOUT] <url> [target_file]
fetch_url() {
    local method="GET" header="" timeout="3"

    while [ $# -gt 0 ]; do
        case "$1" in
            -X) method="$2"; shift 2 ;;
            -H) header="$2"; shift 2 ;;
            -t) timeout="$2"; shift 2 ;;
            *) break ;;
        esac
    done

    local url="${1:-}" target="${2:-}"
    [ -n "$url" ] || return 1

    if [ -n "$target" ]; then
        if _have curl; then
            if [ -n "$header" ]; then
                curl -sSL -X "$method" -H "$header" --max-time "$timeout" "$url" -o "$target" 2>/dev/null
            else
                curl -sSL -X "$method" --max-time "$timeout" "$url" -o "$target" 2>/dev/null
            fi
        elif _have wget; then
            if [ -n "$header" ]; then
                wget -q --method="$method" --header="$header" -T "$timeout" -O "$target" "$url" 2>/dev/null
            else
                wget -q --method="$method" -T "$timeout" -O "$target" "$url" 2>/dev/null
            fi
        elif _have python3; then
            python3 -c '
import sys, urllib.request
url, target, method, hdr, to = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
headers = dict([hdr.split(": ", 1)]) if ": " in hdr else {}
req = urllib.request.Request(url, headers=headers, method=method)
with urllib.request.urlopen(req, timeout=to) as r, open(target, "wb") as f:
    f.write(r.read())
' "$url" "$target" "$method" "$header" "$timeout" 2>/dev/null
        else
            return 1
        fi
    else
        if _have curl; then
            if [ -n "$header" ]; then
                curl -sSL -X "$method" -H "$header" --max-time "$timeout" "$url" 2>/dev/null
            else
                curl -sSL -X "$method" --max-time "$timeout" "$url" 2>/dev/null
            fi
        elif _have wget; then
            if [ -n "$header" ]; then
                wget -q --method="$method" --header="$header" -T "$timeout" -O- "$url" 2>/dev/null
            else
                wget -q --method="$method" -T "$timeout" -O- "$url" 2>/dev/null
            fi
        elif _have python3; then
            python3 -c '
import sys, urllib.request
url, method, hdr, to = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
headers = dict([hdr.split(": ", 1)]) if ": " in hdr else {}
req = urllib.request.Request(url, headers=headers, method=method)
with urllib.request.urlopen(req, timeout=to) as r:
    sys.stdout.buffer.write(r.read())
' "$url" "$method" "$header" "$timeout" 2>/dev/null
        else
            return 1
        fi
    fi
}

# Probe TCP port connectivity on a target host
probe_tcp() {
    local host="$1" port="$2" timeout="${3:-1}"

    if _have nc; then
        nc -z -w "$timeout" "$host" "$port" >/dev/null 2>&1 && return 0
    fi
    if _have timeout; then
        timeout "$timeout" bash -c "</dev/tcp/$host/$port" >/dev/null 2>&1 && return 0
    fi
    if _have python3; then
        python3 -c "import socket, sys; s = socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout=float(sys.argv[3])); s.close()" "$host" "$port" "$timeout" >/dev/null 2>&1 && return 0
    fi
    if _have curl; then
        curl -s --max-time "$timeout" "http://$host:$port" >/dev/null 2>&1 && return 0
    fi
    return 1
}

# Resolve the primary local IPv4 /24 subnet prefix (e.g. 192.168.1)
get_local_subnet() {
    local ip=""

    if _have ip; then
        ip="$(ip -o -f inet addr show 2>/dev/null | awk '/scope global/ {print $4}' | head -n 1 | cut -d/ -f1)"
    fi
    if [ -z "$ip" ] && _have ifconfig; then
        ip="$(ifconfig 2>/dev/null | awk '/inet / && $2 !~ /^127\./ {sub(/^addr:/, "", $2); print $2; exit}')"
    fi
    if [ -z "$ip" ] && _have hostname; then
        ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
    fi

    if [ -n "$ip" ]; then
        printf '%s\n' "$ip" | cut -d. -f1-3
        return 0
    fi
    return 1
}

# =============================================================================
# System, Process, Socket & Filesystem Inspection
# =============================================================================

# List running processes with full command-line arguments
list_processes() {
    ps -eo user,pid,stime,args 2>/dev/null || ps aux 2>/dev/null || ps -ef 2>/dev/null
}

# List network sockets by state ('listening' or 'established')
list_sockets() {
    local mode="${1:-listening}"

    if [ "$mode" = "established" ]; then
        if _have ss; then
            ss -antup 2>/dev/null | grep ESTABLISHED
        elif _have netstat; then
            netstat -antup 2>/dev/null | grep ESTABLISHED
        elif _have lsof; then
            lsof -i -n -P 2>/dev/null | grep ESTABLISHED
        fi
    else
        if _have ss; then
            ss -tunlp 2>/dev/null
        elif _have netstat; then
            netstat -tunlp 2>/dev/null
        elif _have lsof; then
            lsof -i -n -P 2>/dev/null | grep LISTEN
        fi
    fi
}

# Inspect permissions and ownership of directory entries
list_perms() {
    local target="${1:-.}"

    if find . -prune -printf '' >/dev/null 2>&1; then
        find "$target" -maxdepth 1 -printf "$_FIND_PRINTF_PATTERN" 2>/dev/null
    elif _have stat; then
        stat -c '%A %U:%G %n' "$target"/* 2>/dev/null || stat -f '%Sp %Su:%Sg %N' "$target"/* 2>/dev/null
    else
        find "$target" -maxdepth 1 -mindepth 1 -exec ls -ld {} + 2>/dev/null | awk '{print $1, $3":"$4, $9}'
    fi
}

# Format file paths from stdin into semicolon-delimited 'Permissions;Owner:Group;Path' lines
format_perms() {
    local path
    while IFS= read -r path || [ -n "$path" ]; do
        [ -n "$path" ] || continue
        if _have stat; then
            stat -c '%A;%U:%G;%n' "$path" 2>/dev/null || stat -f '%Sp;%Su:%Sg;%N' "$path" 2>/dev/null
        else
            ls -ld "$path" 2>/dev/null | awk '{print $1 ";" $3 ":" $4 ";" $NF}'
        fi
    done
}

# =============================================================================
# Output Formatting & Presentation
# =============================================================================

# Pure AWK implementation of column alignment when column utility is unavailable
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
    }' 2>/dev/null
}

# Ensure column command is available in minimal environments
_have column || column() { _column_fallback "$@"; }

# Print an uppercase underlined section header only when non-empty content is present
label() {
    local title="$1" content="${2:-}" printed=0 line

    if [ -n "$content" ]; then
        printf '\n%s\n' "$(printf '%s' "$title" | tr '[:lower:]' '[:upper:]')"
        printf '%*s\n' "${#title}" '' | tr ' ' '-'
        printf '%s\n' "$content"
        return 0
    fi

    while IFS= read -r line || [ -n "$line" ]; do
        if [ "$printed" -eq 0 ]; then
            printf '\n%s\n' "$(printf '%s' "$title" | tr '[:lower:]' '[:upper:]')"
            printf '%*s\n' "${#title}" '' | tr ' ' '-'
            printed=1
        fi

        printf '%s\n' "$line"
    done
}
