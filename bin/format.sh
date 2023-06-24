#/bin/bash
set -o errexit
set -o nounset
set -o pipefail

usage() {
    cat << EOF
Format files in the project.

Options:
    -d, --debug         Debug mode.
    -h, --help          Print this message.
EOF

}
PROJECT_DIR=$(
    cd $(dirname $0)/.. >/dev/null;
    pwd;
)
cd "$PROJECT_DIR"

parse_args(){
    while [[ "$#" -gt "0" ]]; do
        case $1 in
            -d|--debug)
                set -x
                ;;
            -h|--help)
                usage
                exit 0
        esac
        shift
    done
}

format_python() {
    isort --skip-gitignore --overwrite-in-place --profile black "$PROJECT_DIR"
    black "$PROJECT_DIR"
}

parse_args "$@"
format_python
