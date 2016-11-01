#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 bendikro bro.devel+zfssnaps@gmail.com
#
# This file is part of zfssnaps and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#
from __future__ import print_function

import argparse
import sys

from sh import ErrorReturnCode_1

from util import get_snapshot_match, delete_snapshots, do_snapshots, list_snapshots


def delete(args):
    snapshots = []

    if args.recursive:
        if not args.file_system:
            print("-R can only be specified together with -f")
            sys.exit(0)

        for s in args.snapshots:
            match = get_snapshot_match(s)
            for m in match:
                if m.startswith(args.file_system):
                    snapshots.append(m)
    else:
        for s in args.delete:
            match = get_snapshot_match(s)
            for m in match:
                if args.file_system:
                    if m.startswith("%s@" % args.file_system):
                        snapshots.append(m)
                else:
                    snapshots.append(m)

    snapshots = sorted(snapshots)

    if args.verbose:
        if not args.confirm:
            print("Matching snapshots:")
        else:
            print("Deleting snapshots:")
        for s in snapshots:
            print(" - %s" % s)
        print

    delete_snapshots(args, snapshots)

    if not args.confirm:
        print("To delete these snapshots, rerun with --confirm")


def main():
    argparser = argparse.ArgumentParser(description="Create and delete ZFS snapshots")
    argparser.add_argument("-m", "--message", help="Message to postfix the name of the snapshot.", required=False)
    argparser.add_argument("--no-date", required=False, action='store_true',
                           help="Do not prepend date to name of new snapshots.")
    argparser.add_argument("-l", "--list", help="List snapshots.", required=False, action='store_true')
    argparser.add_argument("-R", "--recursive", required=False, action='store_true',
                           help="Match recursively on filesystems.")
    argparser.add_argument("-s", "--simulate", required=False, action='store_true',
                           help="the commands that would be run without executing.")
    argparser.add_argument("-v", "--verbose", help="the commands.", required=False, action='store_true', default=True)
    argparser.add_argument("-f", "--file-system",  required=False, action='append',
                           help="File systems to operate on. May be given multiple times")
    argparser.add_argument("-c", "--confirm", help="Confirm operation.", required=False, action='store_true')

    group = argparser.add_mutually_exclusive_group(required=False)
    group.add_argument("-d", "--delete",  nargs=1, help="Snapshot to delete.", required=False)
    group.add_argument("-n", "--new", help="Create new snapshot.", required=False, action='store_true')

    args = argparser.parse_args()

    if args.list:
        list_snapshots(args.file_system)
        sys.exit(0)

    if args.new and not args.file_system:
        print("Please specify a file system with -f")
        sys.exit(0)
    if args.new:
        if args.no_date and not args.message:
            print("The --no-date option cannot be used without --message")
            sys.exit()

        new_snapshots = do_snapshots(args)
        if new_snapshots:
            if not args.confirm:
                print("To create these snapshots, rerun with --confirm:")
            else:
                print("Created following snapshots:")
            for s in new_snapshots:
                print("- %s" % s)
        else:
            print("No file systems matched '%s'" % args.file_system[0])

    elif args.delete:
        delete(args)
    else:
        argparser.print_help()


def entry(args=None):
    try:
        main()
    except ErrorReturnCode_1 as ex:
        print("Error:", ex.stderr)


if __name__ == '__main__':
    entry()
    sys.exit()
