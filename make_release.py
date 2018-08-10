#!/usr/bin/env python3

import argparse
import os
import re
import sys
import tempfile
from itertools import chain


def get_current_version(path, verbose):
    package_init = os.path.join(path, 'feanor', '__init__.py')
    if verbose:
        print('Checking package __init__.py at {!r}'.format(package_init))
    with open(package_init, 'rb') as infile:
        for line in infile:
            normalized_line = _normalize_line(line)
            if _is_version_definition_line(normalized_line):
                expr = normalized_line.split(b'=')[1:]
                if len(expr) > 1:
                    raise ValueError('Invalid expression to define version: {!r}'.format(line))
                arguments = re.sub(rb'^[^(]+\((.+)\)\s*$', rb'\1', expr[0]).split(b',')
                if len(arguments) != 5:
                    raise ValueError('Invalid number of arguments.')
                return chain(map(int, arguments[:3]), [arguments[-2][1:-1].decode('ascii'), int(arguments[-1])])
        raise ValueError('Could not find version definition in file {!r}'.format(package_init))


def _normalize_line(line):
    return re.sub(rb'\s+', b'', line).lower()


def _is_version_definition_line(line):
    return line.startswith(b'version_info=')


def write_new_version(path, major, minor, bugfix, level, serial, verbose):
    if verbose:
        print('writing new version: {!r}'.format([major, minor, bugfix, level, serial]))
    package_init = os.path.join(path, 'feanor', '__init__.py')

    with tempfile.TemporaryDirectory() as tmpdir:
        outfile_path = os.path.join(tmpdir, 'outfile.py')
        with open(package_init, 'rb') as init_file, open(outfile_path, 'wb') as outfile:
            for line in init_file:
                if _is_version_definition_line(_normalize_line(line)):
                    new_line = 'version_info = VersionInfo({!r}, {!r}, {!r}, {!r}, {!r})\n'.format(
                        major, minor, bugfix, level, serial
                    )
                    if verbose:
                        print('Changing version line from:\n\t{!r}\nto:\n\t{!r}'.format(line.decode('utf-8'), new_line))
                    outfile.write(new_line.encode('utf-8'))
                else:
                    outfile.write(line)
        if verbose:
            print('Deleting old file {!r}'.format(package_init))
        os.remove(package_init)
        if verbose:
            print('Renaming new file to original file.')
        os.rename(outfile_path, package_init)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-M', '--major', action='store_true', help='Increase the major number of the version.')
    group.add_argument('-m', '--minor', action='store_true', help='Increase the minor number of the version.')
    group.add_argument('-b', '--bugfix', action='store_true', help='Increase the bugfix number of the version.')
    group.add_argument('-s', '--serial', action='store_true', help='Increase the serial number of the version.')
    parser.add_argument('--set-level', dest='level', choices=('alpha', 'beta', 'rc', 'final'),
                        help='Set the level of the release')
    parser.add_argument('--package-path', default='.',
                        help='Path to the directory containing feanor package.\nDefault "." for current directory.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Be verbose.')

    args = parser.parse_args()
    change_num = any([args.major, args.minor, args.bugfix, args.serial])
    if not any([change_num, args.level]):
        parser.print_usage(sys.stderr)
        sys.exit(2)
    try:
        major, minor, bugfix, level, serial = get_current_version(args.package_path, verbose=args.verbose)
        bugfix, major, minor, serial = _increase_version_numbers(args, bugfix, change_num, major, minor, serial)
        level, serial = _change_release_level(args, level, serial)
        if args.verbose:
            print('New version will be {}-{}{}'.format('.'.join(map(str, [major, minor, bugfix])), level, serial))
        write_new_version(args.package_path, major, minor, bugfix, level, serial, verbose=args.verbose)
    except ValueError as e:
        if args.verbose:
            print('ERROR: {}'.format(e), file=sys.stderr)
        sys.exit(1)


def _change_release_level(args, level, serial):
    if args.level and args.level != level:
        if args.verbose:
            print('Changing release level from {!r} to {!r}\nResetting serial to 0.'.format(level, args.level))
        serial = 0
        level = args.level
    return level, serial


def _increase_version_numbers(args, bugfix, change_num, major, minor, serial):
    if change_num:
        if args.serial:
            serial += 1
        else:
            serial = 0
            if args.bugfix:
                bugfix += 1
            else:
                bugfix = 0
                major, minor = (major, minor + 1) if args.minor else (major + 1, 0)
    return bugfix, major, minor, serial


if __name__ == '__main__':
    main()
