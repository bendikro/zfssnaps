from __future__ import print_function

import collections
import datetime
import locale
import logging
import os
import re

import humanfriendly
from sh import grep, zfs

logger = logging.getLogger('zfssnaps')
locale.setlocale(locale.LC_TIME, os.getenv('LC_TIME'))


def parse_size(val):
    """ZFS on FreeBSD returns filesize with punctuation as decimal mark,
    but ZOL uses comma. Replace comma with punctuation
    """
    return humanfriendly.parse_size(val.replace(",", "."), binary=False)


def get_snapshot_match(snapshot_name, filesystems=None):
    """
    Get the snapshot for each filesystems with the given snapshot
    """
    list_args = _get_zfs_list_snapshot_args(filesystems)
    output = grep(zfs.list(list_args), "%s " % snapshot_name)
    lines = output.splitlines()

    matches = []
    for l in lines:
        s = l.split()
        matches.append(s[0])
    return matches


def get_filesystem_list(pattern):
    output = zfs.list("-t", "filesystem")
    fs = get_matches(pattern, output)
    return fs


def get_matches(pattern, output):
    matches = []
    fs_expr = pattern.replace("*", ".*")
    lines = output.splitlines()
    for l in lines:
        s = l.split()[0]
        m = re.match(fs_expr, s)
        if m:
            matches.append(s)
    return matches


def _get_zfs_list_snapshot_args(filesystems, extra_args=None):
    list_args = ["-t", "snapshot"]
    if filesystems:
        list_args.append("-r")
        list_args.extend(filesystems)

    if extra_args:
        list_args.extend(extra_args)
    return list_args


def get_snapshots_list(pattern, filesystems=None):
    list_args = _get_zfs_list_snapshot_args(filesystems)
    output = zfs.list(list_args)
    snaps = get_matches(pattern, output)
    return snaps


def get_command_str(cmd, args):
    return "%s %s" % (cmd, " ".join(args))


def get_snapshots(filesystems=None, extra_args=None, verbose=False):
    list_args = _get_zfs_list_snapshot_args(filesystems, extra_args=extra_args)
    if verbose:
        logger.info(get_command_str("zfs list", list_args))
    output = zfs.list(list_args)
    header = "%s" % output.splitlines()[0]
    return header, output


def list_snapshots(filesystems=None):
    header, output = get_snapshots(filesystems=filesystems)
    print("%s\n%s" % (header, output))


def print_snapshot_groups(by_label, order_by_date):
    base_fmt = "%%(name)-%(max_label)ds   %%(used)-%(max_used)ds   %%(refer)-%(max_refer)ds   %%(filesystems)s"
    max_label = max(len(e) for e in by_label.keys())
    max_used = max(len(humanfriendly.format_size(e["used"], binary=False)) for e in by_label.values())
    max_refer = max(len(humanfriendly.format_size(e["refer"], binary=False)) for e in by_label.values())

    fmt = base_fmt % {"max_label": max_label, "max_used": max_used, "max_refer": max_refer}
    print(fmt % dict(name="LABEL", used="USED", refer="REFER", filesystems="FILESYSTEMS"))

    ordered = by_label
    if order_by_date:
        ordered = collections.OrderedDict(sorted(by_label.items(), key=lambda t: by_label[t[0]]['created'],
                                                 reverse=True))

    for l in ordered.keys():
        print(fmt % dict(name=l,
                         used=humanfriendly.format_size(by_label[l]["used"], binary=False),
                         refer=humanfriendly.format_size(by_label[l]["refer"], binary=False),
                         filesystems=", ".join(by_label[l]["filesystems"])))


def list_snapshot_groups(filesystems=None, order_by_date=False, verbose=False):
    extra_args = ["-o", "name,used,available,referenced,mountpoint,creation"]
    header, output = get_snapshots(filesystems=filesystems, extra_args=extra_args, verbose=verbose)
    by_label = collections.OrderedDict()

    for i, l in enumerate(output.splitlines()):
        #         zroot2@2015.02.20-21:06:18-Upgrade.10                     692K      -   553M  -
        m = re.match(r"(?P<filesystem>.+)@(?P<label>\S+)\s+(?P<used>\S+)\s+"
                     r"(?P<avail>\S+)\s+(?P<refer>\S+)\s+(?P<mountpoint>\S+)\s+(?P<created>.+)", l)
        if m:
            d = m.groupdict()
            created_date_time = datetime.datetime.strptime(d['created'], '%a %b %d %H:%M %Y')
            if not d["label"] in by_label:
                by_label[d["label"]] = {"entries": [], "used": 0, "refer": 0, "created": created_date_time,
                                        "filesystems": []}
            label_d = by_label[d["label"]]
            label_d["entries"].append(d)
            label_d["filesystems"].append(d["filesystem"])
            label_d["used"] = label_d["used"] + parse_size(d["used"])
            label_d["refer"] = label_d["refer"] + parse_size(d["refer"])

    print_snapshot_groups(by_label, order_by_date=order_by_date)


def do_snapshots(args):
    date = datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S")
    new_snapshots = []
    name = ""
    if not args.no_date:
        name = date

    if args.message:
        if name:
            name += "-"
        name += args.message

    for fs in args.file_system:
        if args.recursive:
            matches = get_filesystem_list(fs)
        else:
            matches = [fs]

        if args.file_system_exclude:
            for exclude in args.file_system_exclude:
                if exclude in matches:
                    logger.debug("Excluding filesystem '%s'" % (exclude))
                    matches.remove(exclude)

        for m in matches:
            snapshot = "%s@%s" % (m, name)
            new_snapshots.append(snapshot)
            if args.confirm or args.simulate:
                if args.simulate:
                    print("zfs snapshot %s" % (snapshot))
                else:
                    zfs.snapshot(snapshot)
    return new_snapshots


def delete_snapshots(args, snapshots):
    for s in snapshots:
        snapshot = s
        cmd = "/sbin/zfs destroy %s" % (snapshot)

        if args.confirm or args.simulate:
            if args.simulate:
                print("Simulate removing snapshot: '%s'" % snapshot)
                print(" %s" % cmd)
            else:
                print("Removing snapshot: '%s'" % snapshot)
                zfs.destroy(snapshot)


def rollback_snapshots(args, snapshots):
    for snapshot in snapshots:
        cmd = "/sbin/zfs rollback %s" % (snapshot)
        if args.confirm or args.simulate:
            if args.simulate:
                print("Simulate rollback of snapshot: '%s'" % snapshot)
                print(" %s" % cmd)
            else:
                print("Rolling back snapshot: '%s'" % snapshot)
                zfs.rollback(snapshot)
