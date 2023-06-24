#/bin/bash
set -o errexit
set -o nounset
set -o pipefail

usage() {
    cat << EOF
Install MYMK and a layout on an RP2040 board with CircuitPython installed.

Options:
    -l, --layout NAME   Name of the layout to install on the board.
                        It must match a file in the 'layouts' directory
                        without the '.py' extension.
    --dev               Dev mode.
                        Loop every second and update the layout if changes
                        have been made.
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
    LAYOUT="$PROJECT_DIR/layouts/getting_started.py"
    while [[ "$#" -gt "0" ]]; do
        case $1 in
            -l|--layout)
                shift
                LAYOUT="$PROJECT_DIR/layouts/$1.py"
                ;;
            --dev)
                DEV_MODE="1"
                ;;
            --fast)
                FAST_MODE="1"
                ;;
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

init() {
    CIRCUITPYTHON_VERSION="8.1.0"
    board="sparkfun_pro_micro_rp2040"
    CIRCUITPYTHON_URL="https://downloads.circuitpython.org/bin/$board/en_US/adafruit-circuitpython-$board-en_US-$CIRCUITPYTHON_VERSION.uf2"
    DATE=$(curl -w "%{url_effective}" -I -L -o /dev/null -s -S "https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/latest" | sed 's:.*/::')
    CIRCUITPYTHON_LIB_VERSION="adafruit-circuitpython-bundle-$(echo "$CIRCUITPYTHON_VERSION" | cut -d. -f1).x-mpy-$DATE"
    CIRCUITPYTHON_LIB_URL="https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/$(echo "$CIRCUITPYTHON_LIB_VERSION" | cut -d- -f6)/$CIRCUITPYTHON_LIB_VERSION.zip"
    DRIVE_SOURCE="$PROJECT_DIR/drive"
    mkdir -p "$DRIVE_SOURCE/lib"
    ln -sf "$PROJECT_DIR/mymk" "$DRIVE_SOURCE/"
}

get_drive() {
    unset DRIVE
    DRIVE=$(df | sed "s:.* ::" | grep --extended-regexp "CIRCUITPY|KEYBOARD|RPI-RP2" || true)
}

wait_for_drive() {
    echo -n "[$(date +"%H:%M:%S")] Connect MCU: "
    unset DRIVE
    while [ -z "${DRIVE:-}" ]; do 
        echo -n "."
        sleep 1
        get_drive
    done
    echo "OK ($DRIVE)"
    if [ "$(basename "${DRIVE}")" = "RPI-RP2" ]; then
        install_circuitpython
    fi
    if [ "$(basename "${DRIVE:-RPI-RP2}")" = "CIRCUITPY" ]; then
        rename_drive
    fi

    # Make sure the drive is mounted with noatime, other just reading
    # a file will trigger an auto-reload
    if ! grep "${DRIVE}" "/etc/mtab" | grep -q noatime; then
        echo "Password is required to remount the drive with the right options"
        sudo mount -o remount,noatime "${DRIVE}"
    fi
}

install_circuitpython() {
    echo -n "[$(date +"%H:%M:%S")] Install CircuitPython: "
    curl --fail --location --output "$DRIVE/circuitpython.uf2" --silent "$CIRCUITPYTHON_URL"

    # Wait for MCU to be back online
    while [ "$(basename "${DRIVE:-RPI-RP2}")" = "RPI-RP2" ]; do
        echo -n "."
        sleep 1
        get_drive
    done
    echo "OK"
}

rename_drive() {
    cat <<EOF
New keyboard found. How do you want to configure it?
s) Single board keyboard
l) Split keyboard, left side
r) Split keyboard, right side
EOF
    while true; do
        read -r -p "Choice: " answer
        case $answer in
            l)
                SUFFIX="-L"
                break
                ;;
            r)
                SUFFIX="-R"
                break
                ;;
            s)
                break
                ;;
        esac
    done
    echo "Renaming the drive requires you to enter your password."
    sudo mlabel -i "$(df "$DRIVE" | tail -1 | cut -d" " -f1)" ::"KEYBOARD${SUFFIX:-}"
    sudo chown -R "$(whoami):$(groups | cut -d ' ' -f1)" "$DRIVE"
}

get_libs() {
    echo -n "[$(date +"%H:%M:%S")] Get libraries: "
    LIB_DIR="$PROJECT_DIR/lib"
    if [ ! -e "$LIB_DIR" ] || [ "$CIRCUITPYTHON_LIB_VERSION" != "$(cat "$LIB_DIR/version.txt")" ]; then
        tmp_dir="$(mktemp -d)"
        curl --fail --location --output "$tmp_dir/adafruit-libs.zip" --silent "$CIRCUITPYTHON_LIB_URL"
        unzip -o "$tmp_dir/adafruit-libs.zip" -d "$tmp_dir">/dev/null
        echo -n "$CIRCUITPYTHON_LIB_VERSION" > "$tmp_dir/$CIRCUITPYTHON_LIB_VERSION/lib/version.txt"
        if [ -e "$LIB_DIR" ]; then
            rm -rf "$LIB_DIR"
        fi
        mv "$tmp_dir/$CIRCUITPYTHON_LIB_VERSION/lib" "$LIB_DIR"
        rm -rf "$tmp_dir"
    fi
    lib_list=(
        "adafruit_hid"
        "neopixel"
    )
    # Copying the libs will trigger an auto-reload
    for lib in "${lib_list[@]}"; do
        echo -n "."
        if [ -e "$LIB_DIR/$lib.mpy" ]; then
            lib="$lib.mpy"
        fi
        ln -sf "$LIB_DIR/$lib" "$DRIVE_SOURCE/lib/"
    done
    echo "OK"
}

sync_drive() {
    if [ $(
        rsync --checksum --copy-links --delete --dry-run --recursive --verbose \
        "$DRIVE_SOURCE/" "$DRIVE" | wc -l
        ) != "4" ]; then
        echo -n "[$(date +"%H:%M:%S")] Install to drive: "
        rsync --archive --copy-links --delete "$DRIVE_SOURCE/" "$DRIVE"
        sync
        echo "OK"
        tput bel
    fi
}

install_layout() {
    ln -sf "$LAYOUT" "$DRIVE_SOURCE/code.py"
}

install_drive() {
    wait_for_drive
}

parse_args "$@"
init
if [ -z "${FAST_MODE:-}" ]; then
    get_libs
fi
if [ -z "${DEV_MODE:-}" ]; then
    install_drive
    install_layout
    sync_drive
else
    while true; do
        install_drive
        install_layout
        while [ -n "${DRIVE:-}" ]; do
            sync_drive
            sleep 1 || exit 0
            get_drive || true
        done
    done
fi
