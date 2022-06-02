#!/usr/bin/env python3

from sea33 import C8033Raw


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="C8033 command line interface")
    _args = parser.parse_args()

    c33 = C8033Raw()
    c33.print_status()


if __name__ == "__main__":
    main()
