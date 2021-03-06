#!/usr/bin/env python3

from sea33 import C8033Raw


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="C8033 command line interface")
    _args = parser.parse_args()

    c33 = C8033Raw()
    print("Type HLP for help")
    print("Waiting for input...")
    while True:
        print("> ", end="")
        l = input().strip()
        rx = c33.cmd(l)
        rx = rx.replace("\r", "\n")
        print(rx)


if __name__ == "__main__":
    main()
