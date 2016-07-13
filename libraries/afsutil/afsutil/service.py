# Copyright (c) 2014-2015 Sine Nomine Associates
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

"""Helper to start and stop afs services."""

import os
import logging

from afsutil.system import run, is_afs_mounted, afs_umount, unload_module, get_running, is_running

logger = logging.getLogger(__name__)

COMPONENTS = ['client', 'server']

def check_component_names(components):
    """Raises a value error if an unknown component name is given."""
    ALL = set(COMPONENTS)
    if components is None:
        c = ALL
    else:
        c = set(components)        # remove duplicates
    unknown = c.difference(ALL)    # find unknowns
    if unknown:
        s = 's' if len(unknown) > 1 else ''
        unknown = ', '.join(unknown)
        raise ValueError("Unknown component%s: %s" % (s, unknown))
    return list(c)

def _rc(component, action):
    rc = "/etc/init.d/openafs-%s" % (component)
    if not os.path.isfile(rc):
        raise AssertionError("Init script is missing! %s" % (rc))
    run(rc, args=[action])

def start(**kwargs):
    components = check_component_names(kwargs['components'])
    if 'server' in components:
        if not is_running('bosserver'):
            _rc('server', 'start')
    if 'client' in components:
        if not is_afs_mounted():
            _rc('client', 'start')

def stop(**kwargs):
    components = check_component_names(kwargs['components'])
    if 'client' in components:
        if is_afs_mounted():
            _rc('client', 'stop')
        afs_umount() # Be sure afs is unmounted before trying to unload.
        unload_module()
    if 'server' in components:
        if is_running('bosserver'):
            _rc('server', 'stop')
        servers = ('bosserver', 'upserver', 'upclient',
                   'buserver', 'bucoord', 'butc',
                   'vlserver', 'ptserver',
                   'fileserver', 'volserver',
                   'dafileserver', 'davolserver', 'salvageserver')
        still_running = get_running().intersection(servers)
        if still_running:
            raise AssertionError("Servers still running! %s" % (" ".join(list(still_running))))

