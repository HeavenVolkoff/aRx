#!/usr/bin/env bash

# ----- Read only properties ---------------------------------------------------

readonly __scriptbase="$( cd $( dirname ${BASH_SOURCE[0]})  && pwd)"
readonly __scriptname="$(basename ${0})"
readonly __this="${__scriptbase}/${__scriptname}"

# --- Command Interpreter Configuration ----------------------------------------

set -e    # exit immediate if an error occurs in a pipeline
set -u    # don't allow not set variables to be utilized
set -o pipefail  # trace ERR through pipes
set -o errtrace  # trace ERR through 'time command' and other functions
# set -x  			# Uncomment to debug this shell script
# set -n  			# Uncomment to check your syntax, without execution.

if [[ -z ${1+x} ]]; then
    echo >&2 "Missing argument"
    exit -1
fi

read_config()  {
    echo "$("$__scriptbase/read_config.py" "$__scriptbase/../.editorconfig" "$1" "$2")"
}

for file in "$@"; do
    if [[ ! -f "$file" ]]; then
        echo >&2 "$file: Don't exist"
        exit -1
    fi

    filename="$(basename -- "$file")"
    file_ext="${filename##*.}"

    if [[ "$file_ext" == "py" ]]; then
        if ! { hash isort && hash black; }; then
            echo >&2 "Python: isort and black are not installed"
            exit -1
        fi

        import_sorted="$(isort -q -ac "$file" -d)"
        if [[ -z "$import_sorted" ]]; then
            import_sorted="$(cat "$file")"
        fi

        formatted="$(echo "$import_sorted" | black --config "$(read_config "**.py" black_file)" -)"
    elif [[ "$file_ext" == "sh" ]]; then
        if ! hash shfmt; then
            echo >&2 "Bash: shfmt are not installed"
            exit -1
        fi

        formatted="$(shfmt -i "$(read_config "**.sh" indent_size)" -ci -kp "$file")"
    else
        echo >&2 "$file: Don't have a recognizable extension"
        continue
    fi

    echo "$formatted" >"$file"
    echo "$file: Formatted"
done
