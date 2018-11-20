#!/usr/bin/env python3

# Internal
from configparser import ConfigParser
import sys

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Missing arguments", file=sys.stderr)
        sys.exit(-1)

    from itertools import chain

    parser = ConfigParser()
    with open(sys.argv[1], encoding="utf8") as config_file:
        fixed_config_file = chain(("[__TOP__]",), config_file)
        parser.read_file(fixed_config_file)

    print(parser.get(sys.argv[2], sys.argv[3], fallback=""))
