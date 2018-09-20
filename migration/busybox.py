# This code is stolen directly from lxd-images, for expediency's sake.
import atexit
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import uuid


def find_on_path(command):
    """Is command on the executable search path?"""

    if 'PATH' not in os.environ:
        return False
    path = os.environ['PATH']
    for element in path.split(os.pathsep):
        if not element:
            continue
        filename = os.path.join(element, command)
        if os.path.isfile(filename) and os.access(filename, os.X_OK):
            return True
    return False


class Busybox(object):
    workdir = None

    def __init__(self):
        # Create our workdir
        self.workdir = tempfile.mkdtemp()

    def cleanup(self):
        if self.workdir:
            shutil.rmtree(self.workdir)

    def create_tarball(self, split=False):
        xz = "pxz" if find_on_path("pxz") else "xz"

        destination_tar = os.path.join(self.workdir, "busybox.tar")
        target_tarball = tarfile.open(destination_tar, "w:")

        if split:
            destination_tar_rootfs = os.path.join(self.workdir,
                                                  "busybox.rootfs.tar")
            target_tarball_rootfs = tarfile.open(destination_tar_rootfs, "w:")

        metadata = {'architecture': os.uname()[4],
                    'creation_date': int(os.stat("/bin/busybox").st_ctime),
                    'properties': {
                        'os': "Busybox",
                        'architecture': os.uname()[4],
                        'description': "Busybox %s" % os.uname()[4],
                        'name': "busybox-%s" % os.uname()[4],
                        # Don't overwrite actual busybox images.
                        'obfuscate': str(uuid.uuid4()), },
                    }

        # Add busybox
        with open("/bin/busybox", "rb") as fd:
            busybox_file = tarfile.TarInfo()
            busybox_file.size = os.stat("/bin/busybox").st_size
            busybox_file.mode = 0o755
            if split:
                busybox_file.name = "bin/busybox"
                target_tarball_rootfs.addfile(busybox_file, fd)
            else:
                busybox_file.name = "rootfs/bin/busybox"
                target_tarball.addfile(busybox_file, fd)

        # Add symlinks
        busybox = subprocess.Popen(["/bin/busybox", "--list-full"],
                                   stdout=subprocess.PIPE,
                                   universal_newlines=True)
        busybox.wait()

        for path in busybox.stdout.read().split("\n"):
            if not path.strip():
                continue

            symlink_file = tarfile.TarInfo()
            symlink_file.type = tarfile.SYMTYPE
            symlink_file.linkname = "/bin/busybox"
            if split:
                symlink_file.name = "%s" % path.strip()
                target_tarball_rootfs.addfile(symlink_file)
            else:
                symlink_file.name = "rootfs/%s" % path.strip()
                target_tarball.addfile(symlink_file)

        # Add directories
        for path in ("dev", "mnt", "proc", "root", "sys", "tmp"):
            directory_file = tarfile.TarInfo()
            directory_file.type = tarfile.DIRTYPE
            if split:
                directory_file.name = "%s" % path
                target_tarball_rootfs.addfile(directory_file)
            else:
                directory_file.name = "rootfs/%s" % path
                target_tarball.addfile(directory_file)

        # Add the metadata file
        metadata_yaml = json.dumps(metadata, sort_keys=True,
                                   indent=4, separators=(',', ': '),
                                   ensure_ascii=False).encode('utf-8') + b"\n"

        metadata_file = tarfile.TarInfo()
        metadata_file.size = len(metadata_yaml)
        metadata_file.name = "metadata.yaml"
        target_tarball.addfile(metadata_file,
                               io.BytesIO(metadata_yaml))

        # Add an /etc/inittab; this is to work around:
        # http://lists.busybox.net/pipermail/busybox/2015-November/083618.html
        # Basically, since there are some hardcoded defaults that misbehave, we
        # just pass an empty inittab so those aren't applied, and then busybox
        # doesn't spin forever.
        inittab = tarfile.TarInfo()
        inittab.size = 1
        inittab.name = "/rootfs/etc/inittab"
        target_tarball.addfile(inittab, io.BytesIO(b"\n"))

        target_tarball.close()
        if split:
            target_tarball_rootfs.close()

        # Compress the tarball
        r = subprocess.call([xz, "-9", destination_tar])
        if r:
            raise Exception("Failed to compress: %s" % destination_tar)

        if split:
            r = subprocess.call([xz, "-9", destination_tar_rootfs])
            if r:
                raise Exception("Failed to compress: %s" %
                                destination_tar_rootfs)
            return destination_tar + ".xz", destination_tar_rootfs + ".xz"
        else:
            return destination_tar + ".xz"


def create_busybox_image():
    busybox = Busybox()
    atexit.register(busybox.cleanup)

    path = busybox.create_tarball()

    with open(path, "rb") as fd:
        fingerprint = hashlib.sha256(fd.read()).hexdigest()

    return path, fingerprint
