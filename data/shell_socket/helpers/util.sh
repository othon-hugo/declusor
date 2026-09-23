_FIND_PRINTF_PATTERN='%-12M %u:%-10g %p\n'
_FIND_PRINTF_SEPARATOR_PATTERN='%M;%u:%g;%p\n'

print_with_label() {
    title="$1"

    while IFS= read -r line; do
        if [ ${title+x} ]; then
            echo
            echo $title | tr '[:lower:]' '[:upper:]'
            echo $(head -c ${#title} < /dev/zero | tr '\0' '-')

            unset title
        fi

        echo "$line"
    done
}

if ! command -v column >/dev/null 2>&1; then
    column() {
        local sep=" "
        local table=0

        while [[ $# -gt 0 ]]; do
            case "$1" in
                -t) table=1 ;;
                -s)
                    shift
                    sep="$1"
                    ;;
                *)
                    ;;
            esac
            shift
        done

        if [[ "$table" -eq 0 ]]; then
            awk -v FS="$sep" '{$1=$1; print}' 
            return
        fi

        awk -v FS="$sep" '
        {
            for (i = 1; i <= NF; i++) {
                if (length($i) > max[i])
                    max[i] = length($i)
                cell[NR, i] = $i
            }
            if (NF > cols) cols = NF
            rows = NR
        }
        END {
            for (r = 1; r <= rows; r++) {
                for (c = 1; c <= cols; c++) {
                    val = cell[r, c]
                    # padded print
                    printf "%-*s", max[c] + 2, val
                }
                printf "\n"
            }
        }'
    }
fi
