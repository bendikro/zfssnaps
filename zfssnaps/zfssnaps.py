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

from . import util
from .log import setup_logging

setup_logging()


def delete(args):
    snapshots = []

    if args.recursive:
        if not args.file_system:
            print("-R can only be specified together with -f")
            sys.exit(0)

        for s in args.delete:
            match = util.get_snapshot_match(s, filesystems=args.file_system)
            for m in match:
                for file_system in args.file_system:
                    if m.startswith(file_system):
                        snapshots.append(m)
    else:
        for s in args.delete:
            match = util.get_snapshot_match(s, filesystems=args.file_system)
            for m in match:
                if args.file_system:
                    for file_system in args.file_system:
                        if m.startswith("%s@" % file_system):
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

    util.delete_snapshots(args, snapshots)

    if not args.confirm:
        print("To delete these snapshots, rerun with --confirm")


def rollback(args):
    snaps = util.get_snapshots_list(args.rollback, filesystems=args.file_system)

    if not snaps:
        print("No filesystem snapshots matched")
        return

    print("Rolling back snapshots:")
    for snap in snaps:
        print(" - %s" % snap)

    util.rollback_snapshots(args, snaps)

    if not args.confirm:
        print("To rollback to these snapshots, rerun with --confirm")


def main():
    argparser = argparse.ArgumentParser(description="Create and delete ZFS snapshots")
    argparser.add_argument("-m", "--message", required=False,
                           help="Message to postfix the name of the snapshot.")
    argparser.add_argument("--no-date", required=False, action='store_true',
                           help="Do not prepend date to name of new snapshots.")
    argparser.add_argument("-R", "--recursive", required=False, action='store_true',
                           help="Match recursively on filesystems.")
    argparser.add_argument("-s", "--simulate", required=False, action='store_true',
                           help="the commands that would be run without executing.")
    argparser.add_argument("-v", "--verbose", required=False, action='store_true', default=True,
                           help="the commands.")
    argparser.add_argument("--version", help="the commands.", required=False, action='store_true', default=False)
    argparser.add_argument("-fsp", "--file-system-property",  required=False, action='store',
                           help="File system property with optional value (key=value)")
    argparser.add_argument("-f", "--file-system",  required=False, action='append',
                           help="File systems to operate on. May be given multiple times")
    argparser.add_argument("-fe", "--file-system-exclude",  required=False, action='append',
                           help="File systems to exclude. May be given multiple times")
    argparser.add_argument("-c", "--confirm", required=False, action='store_true', help="Confirm operation.")

    group = argparser.add_mutually_exclusive_group(required=False)
    group.add_argument("-d", "--delete",  metavar='<snapshot>', nargs=1, required=False,
                       help=("Snapshot to delete. This is a grep pattern that must match the output "
                             "from 'zfs list -t snapshot'"))
    group.add_argument("-n", "--new", required=False, action='store_true', help="Make NEW snapshot.")
    group.add_argument("-rb", "--rollback",  required=False,
                       help="Rollback filesystem snapshot matching the pattern. Use asterix to match anything")
    group.add_argument("-l", "--list", required=False, action='store_true', help="List snapshots.")
    group.add_argument("-lsl", "--list-snapshot-labels", required=False, action='store_true',
                       help="List snapshots grouped by label.")
    group.add_argument("-lsld", "--list-snapshot-labels-by-date", required=False, action='store_true',
                       help="List snapshots grouped by label, ordered by created date", )
    group.add_argument("-lfs", "--list-filesystems", required=False, action='store_true',
                       help="List filesystems")


    args = argparser.parse_args()

    if args.version:
        from . import __version__
        print(__version__)
        sys.exit(0)
    if args.list:
        util.list_snapshots(filesystems=args.file_system, recursive=args.recursive,
                            fs_property=args.file_system_property)
        sys.exit(0)
    elif args.list_snapshot_labels or args.list_snapshot_labels_by_date:
        util.list_snapshot_groups(filesystems=args.file_system, recursive=args.recursive,
                                  fs_property=args.file_system_property,
                                  order_by_date=args.list_snapshot_labels_by_date,
                                  verbose=args.verbose)
        sys.exit(0)
    elif args.list_filesystems:
        util.print_filesystems(args.file_system, fs_property_value=args.file_system_property)
        sys.exit(0)

    if args.new and not args.file_system:
        print("Please specify a file system with -f")
        sys.exit(0)

    if args.new:
        if args.no_date and not args.message:
            print("The --no-date option cannot be used without --message")
            sys.exit()

        new_snapshots = util.do_snapshots(args)
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
    elif args.rollback:
        rollback(args)
    else:
        util.cprint("Operation missing. Must be one of -d, -n, -rb", color='red')
        argparser.print_help()
        #print("group:", dir(group))
        #print("group.prefix_chars:", group.prefix_chars)
        #print("group.prefix_chars:", group.__dict__)
        #print("_mutually_exclusive_groups:", dir(group._mutually_exclusive_groups))


def entry(args=None):
    try:
        main()
    except ErrorReturnCode_1 as ex:
        print("Error:", ex)


if __name__ == '__main__':
    entry()
    sys.exit()
