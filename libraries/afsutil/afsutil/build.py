# Copyright (c) 2014-2016 Sine Nomine Associates
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Helper to build OpenAFS for development and testing."""

import logging
import os
import sys
import shlex
from afsutil.system import sh, CommandFailed

logger = logging.getLogger(__name__)

DEFAULT_CF = [
    '--enable-debug',
    '--enable-debug-kernel',
    '--disable-optimize',
    '--disable-optimize-kernel',
    '--without-dot',
]

def _sanity_check_dir():
    msg = "Missing '%s'; are you in the OpenAFS source top-level directory?"
    for d in ('src', 'src/afs', 'src/viced'):
        if not os.path.isdir(d):
            raise AssertionError(msg % (d))

def _allow_git_clean():
    clean = False
    try:
        output = sh('git', 'config', '--bool', '--get', 'afsutil.clean', output=True)
        if output[0] == 'true':
            clean = True
    except CommandFailed as e:
        if e.code == 1:
            logger.info("To enable git clean before builds:")
            logger.info("    git config --local afsutil.clean true");
        else:
            raise e
    return clean

def _clean():
    if os.path.isdir('.git'):
        if _allow_git_clean():
            sh('git', 'clean', '-f', '-d', '-x', '-q')
    else:
        if os.path.isfile('./Makefile'):
            sh('make', 'clean')

def _make_srpm():
    # Get the filename of the generated source rpm from the output of the
    # script. The source rpm filename is needed to build the rpms.
    output = sh('make', 'srpm', output=True)
    for line in output:
        if line.startswith('SRPM is '):
            return line.split()[2]
    raise CommandFailed('make', ['srpm'], 1, '', 'Failed to get the srpm filename.')

def _make_rpm(srpm):
    # These commands should probably be moved to the OpenAFS Makefile.
    cwd = os.getcwd()
    arch = os.uname()[4]
    # Build kmod packages.
    packages = sh('rpm', '-q', '-a', 'kernel-devel', output=True)
    for package in packages:
        kernvers = package.lstrip('kernel-devel-')
        logger.info("Building kmod rpm for kernel version %s." % (kernvers))
        sh('rpmbuild',
            '--rebuild',
            '-ba',
            '--target=%s' % (arch),
            '--define', '_topdir %s/packages/rpmbuild' % (cwd),
            '--define', 'build_userspace 0',
            '--define', 'build_modules 1',
            '--define', 'kernvers %s' % (kernvers),
            'packages/%s' % (srpm))
    # Build userspace packages.
    logger.info("Building userspace rpms.")
    sh('rpmbuild',
        '--rebuild',
        '-ba',
        '--target=%s' % (arch),
        '--define', '_topdir %s/packages/rpmbuild' % (cwd),
        '--define', 'build_userspace 1',
        '--define', 'build_modules 0',
        'packages/%s' % (srpm))
    logger.info("Packages written to %s/packages/rpmbuild/RPMS/%s" % (cwd, arch))

def build(cf=None, target='all', clean=True, transarc=True, **kwargs):
    """Build the OpenAFS binaries.

    Build the transarc-path compatible bins by default, which are
    deprecated, but old habits die hard.
    """
    if cf is None:
        cf = DEFAULT_CF
    else:
        cf = shlex.split(cf)  # Note: shlex handles quoting properly.
    if os.uname()[0] == "Linux":
        cf.append('--enable-checking')
    if transarc and not '--enable-transarc-paths' in cf:
        cf.append('--enable-transarc-paths')

    # Sadly, the top-level target depends on the mode we are
    # building.
    if target == 'all' and '--enable-transarc-paths' in cf:
        target = 'dest'

    _sanity_check_dir()
    if clean:
        _clean()
    sh('./regen.sh')
    sh('./configure', *cf)
    sh('make', target)

def package(clean=True, package=None, **kwargs):
    """Build the OpenAFS rpm packages."""
    # The rpm spec file contains the configure options for the actual build.
    # We run configure here just to bootstrap the process.
    if clean:
        _clean()
    sh('./regen.sh', '-q')
    sh('./configure')
    sh('make', 'dist')
    srpm = _make_srpm()
    _make_rpm(srpm)
