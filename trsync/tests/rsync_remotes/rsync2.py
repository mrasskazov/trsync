# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016, Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import os
import shutil
import signal
import socket

from jinja2 import Template
from time import sleep

from trsync.utils import shell as shell
from trsync.utils.utils import bunch as bunch


logging.basicConfig()
log = logging.getLogger(__name__ + 'Instance')
log.setLevel('DEBUG')


class Instance(object):

    """Provide an temporal rsync daemon on custom port"""

    def __init__(self, name):
        self._log = log.getChild(name)
        self._name = name
        self._root_dir = '/tmp/trsync_test/rsync2'
        self._data_dir = os.path.join(self._root_dir, name)

        self._cfg = bunch()
        self._cfg.module = name
        self._cfg.comment = 'rsyncd instance for {}'.format(self._name)
        self._cfg.path = os.path.join(self._data_dir, self._name)
        self._cfg.hosts_allow = 'localhost 127.0.0.1'
        self._cfg.port = self._get_port()
        self._cfg.pid_file = os.path.join(self._data_dir, self._name + '.pid')
        self._cfg.config = os.path.join(self._data_dir, self._name + '.conf')

        self._init_files()
        self._run()

    def _run(self):

        sh = shell.Shell()
        self._cmd = '/usr/bin/rsync --verbose --daemon --port {} --config {}'\
            ''.format(self._cfg.port, self._cfg.config)
        self._log.debug('Starting rsync daemon "{}"'.format(self._cmd))
        sh.shell(self._cmd)
        retry_time = 3.0
        sleep_time = 0.0
        while not os.path.isfile(self._cfg.pid_file):
            sleep(0.2)
            sleep_time += 0.2
            if sleep_time >= retry_time:
                raise RuntimeError('pid-file "{}" not found'
                                   ''.format(self._cfg.pid_file))
        self._pid = int(open(self._cfg.pid_file).read().strip())

    def stop(self):
        self._log.debug('Stoping rsync daemon "%s" (PID=%d)',
                        self._cmd, self._pid)
        os.kill(self._pid, signal.SIGTERM)
        if os.path.isdir(self._data_dir):
            self._log.debug('Removed directory "%s"', self._data_dir)
            shutil.rmtree(self._data_dir)

    @property
    def url(self):
        return 'rsync://localhost:{port}/{module}'.format(**self._cfg)

    @property
    def path(self):
        return self._cfg.path

    def _get_config(self):
        tpl_path, _ = os.path.split(os.path.realpath(__file__))
        template = Template(open(os.path.join(tpl_path, 'rsync2.conf')).read())
        return template.render(**self._cfg)

    def _get_port(self):
        portrange = [
            int(_) for _
            in open('/proc/sys/net/ipv4/ip_local_port_range').read().split()
        ]
        self._log.debug('Portrange is %s' % portrange)
        for port in xrange(*portrange):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._log.debug('Trying to use port %d...' % port)
            result = sock.connect_ex(('127.0.0.1', port))
            self._log.debug('Result is %d' % result)
            if result != 0:
                self._log.debug('Port %s assigned', port)
                return port
            else:
                self._log.debug('Port %d in use', port)
        else:
            raise RuntimeError("Can't assign port number for rsyncd")

    def _init_files(self):
        if os.path.isdir(self._data_dir):
            self._log.debug('Directory %s already exists. Removing...'
                            '', self._data_dir)
            shutil.rmtree(self._data_dir)
        self._log.debug('Creating module directory %s', self.path)
        os.makedirs(self.path)
        self._log.debug('Creating config %s', self._cfg.config)
        with open(self._cfg.config, 'w') as config_file:
            config_file.write(self._get_config())
