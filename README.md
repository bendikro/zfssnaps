zfssnap - A simple CLI tool for snapshots in ZFS
================================================


Changlog
========

1.1.2 - 15.07.2019
------------------

Pass the filesystem arguments to 'zfs list' command when available
to improve speed retrieving snapshots.

1.1.1 - 22.03.2017
------------------

Fix bug with -l not honoring -f option

1.1.0 - 06.03.2017
------------------

Add option -lsl to list snaptshots grouped by label

1.0.0 - 04.10.2016
------------------
Initial release

Supports:
* List snapshots
* Create snapshots
* Delete snapshots (Recursively)
