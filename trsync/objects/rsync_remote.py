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

from trsync.utils import utils as utils

from trsync.objects.rsync_ops import RsyncOps
from trsync.utils.tempfiles import TempFiles

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel('DEBUG')


class RsyncRemote(object):
    def __init__(self,
                 rsync_url,
                 rsync_extra_params='',
                 init_directory_structure=True,
                 ):
        self._log = utils.logger.getChild('RsyncRemote.' + rsync_url)
        self._tmp = TempFiles()
        self.rsync = RsyncOps(
            rsync_url,
            rsync_extra_params=' '.join(['-v --no-owner --no-group',
                                         rsync_extra_params])
        )
        self.url = self.rsync.url
        if init_directory_structure is True:
            self._init_directory_structure()

    def _init_directory_structure(self):
        dir_full_name = self.url.a_dir(self.url.path)
        if dir_full_name not in ['', '/']:
            if self.url.url_type != 'path':
                rsync_root = RsyncOps(self.url.root)
                rsync_root.mk_dir(dir_full_name)
            else:
                if not os.path.isdir(dir_full_name):
                    os.makedirs(dir_full_name)
        return True

    def push(self, source, repo_name='', extra=None):
        '''Push source to destination'''
        opts = '--archive --force --ignore-errors --delete'
        self._log.info('Push "{}" to "{}"'.format(source, repo_name))
        return self.rsync.push(source=source,
                               dest=repo_name,
                               opts=opts,
                               extra=extra)
