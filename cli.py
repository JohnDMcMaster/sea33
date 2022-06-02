#!/usr/bin/env python3

from sea33 import C8033


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="C8033 command line interface")
    _args = parser.parse_args()

    # ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=0, writeTimeout=0)
    c33 = C8033()
    c33.wait_rx()
    print("Type HLP for help")
    print("Waiting for input...")
    while True:
        print("> ", end="")
        l = input().strip()
        c33.send_line(l)
        rx = c33.wait_rx()
        rx = rx.replace("\r", "\n")
        print(rx)


if __name__ == "__main__":
    main()
