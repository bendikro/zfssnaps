from __future__ import print_function

import collections
import datetime
import re

import humanfriendly
from sh import zfs, grep


def get_snapshot_match(snapshot_name):
    matches = []
    output = grep(zfs.list("-t", "snapshot"), "%s " % snapshot_name)
    lines = output.splitlines()
    for l in lines:
        s = l.split()
        matches.append(s[0])
    return matches


def get_filesystem_match(fs_name):
    matches = []
    fs_expr = fs_name.replace("*", ".*")
    output = zfs.list("-t", "filesystem")
    lines = output.splitlines()
    for l in lines:
        s = l.split()[0]
        m = re.match(fs_expr, s)
        if m:
            matches.append(s)
    return matches


def get_snapshots(filesystems=None):
    output = zfs.list("-t", "snapshot")
    if filesystems:
        output_fs = ""
        for fs in filesystems:
            output_fs += grep(output, fs).stdout
        output = output_fs
    return output


def list_snapshots(filesystems=None):
    output = get_snapshots(filesystems=None)
    print(output)


def print_snapshot_groups(by_label):
    base_fmt = "%%(name)-%(max_label)ds   %%(used)-%(max_used)ds   %%(refer)-%(max_refer)ds   %%(filesystems)s"
    max_label = max(len(e) for e in by_label.keys())
    max_used = max(len(humanfriendly.format_size(e["used"], binary=False)) for e in by_label.values())
    max_refer = max(len(humanfriendly.format_size(e["refer"], binary=False)) for e in by_label.values())

    fmt = base_fmt % {"max_label": max_label, "max_used": max_used, "max_refer": max_refer}
    print(fmt % dict(name="LABEL", used="USED", refer="REFER", filesystems="FILESYSTEMS"))
    for l in by_label.keys():
        print(fmt % dict(name=l,
                         used=humanfriendly.format_size(by_label[l]["used"], binary=False),
                         refer=humanfriendly.format_size(by_label[l]["refer"], binary=False),
                         filesystems=", ".join(by_label[l]["filesystems"])))


def list_snapshot_groups(filesystems=None):
    output = get_snapshots(filesystems=None)
    by_label = collections.OrderedDict()
    for i, l in enumerate(output.splitlines()):
        #         zroot2@2015.02.20-21:06:18-Upgrade.10                     692K      -   553M  -
        m = re.match("(?P<filesystem>.+)@(?P<label>\S+)\s+(?P<used>\S+)\s+(?P<avail>\S+)\s+(?P<refer>\S+)\s+(?P<mountpoint>\S+)", l)
        if m:
            d = m.groupdict()
            if not d["label"] in by_label:
                by_label[d["label"]] = {"entries": [], "used": 0, "refer": 0, "filesystems": []}
            label_d = by_label[d["label"]]
            label_d["entries"].append(d)
            label_d["filesystems"].append(d["filesystem"])
            label_d["used"] = label_d["used"] + humanfriendly.parse_size(d["used"], binary=False)
            label_d["refer"] = label_d["refer"] + humanfriendly.parse_size(d["refer"], binary=False)

    print_snapshot_groups(by_label)


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
            matches = get_filesystem_match(fs)
        else:
            matches = [fs]

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
