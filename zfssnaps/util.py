import datetime
import re

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
    output = grep(zfs.list("-t", "filesystem"), "%s " % fs_name)
    lines = output.splitlines()
    for l in lines:
        s = l.split()[0]
        m = re.match(fs_expr, s)
        if m:
            matches.append(s)
    return matches

def list_snapshots(filesystems=None):
    output = zfs.list("-t", "snapshot")
    if filesystems:
        output_fs = ""
        for fs in filesystems:
            output_fs += grep(output, fs).stdout
        output = output_fs
    print output


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
                    print "zfs snapshot %s" % (snapshot)
                else:
                    zfs.snapshot(snapshot)
    return new_snapshots


def delete_snapshots(args, snapshots):
    for s in snapshots:
        snapshot = s
        cmd = "/sbin/zfs destroy %s" % (snapshot)

        if args.confirm or args.simulate:
            if args.simulate:
                print "Simulate removing snapshot: '%s'" % snapshot
                print " %s" % cmd
            else:
                print "Removing snapshot: '%s'" % snapshot
                zfs.destroy(snapshot)
