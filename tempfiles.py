#-*- coding: utf-8 -*-

import os
import shutil
import tempfile

import utils


class TempFiles(object):
    def __init__(self):
        self.logger = utils.logger.getChild('TempFiles')
        self._temp_dirs = list()
        self.empty_dir

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.__del__()

    def __del__(self):
        for d in self._temp_dirs:
            if os.path.isdir(d):
                shutil.rmtree(d)
                self.logger.debug('Removed temporary directory "{}"'.format(d))

    @property
    def empty_dir(self):
        if self.__dict__.get('_empty_dir') is None:
            self._empty_dir = self.get_temp_dir()
        return self._empty_dir

    def get_temp_dir(self, subdirs=None):
        temp_dir = tempfile.mkdtemp()
        self._temp_dirs.append(temp_dir)
        msg = 'Created temporary directory "{}"'.format(temp_dir)
        if subdirs is not None:
            self.create_subdirs(subdirs, temp_dir)
            msg += ' including subdirs "{}"'.format(subdirs)
        self.logger.debug(msg)
        return temp_dir

    def create_subdirs(self, subdirs, temp_dir):
        if not os.path.isdir(temp_dir):
            temp_dir = self.get_temp_dir()
        if subdirs is not None:
            if type(subdirs) == str:
                _ = subdirs
                subdirs = list()
                subdirs.append(_)
            if type(subdirs) in (list, tuple):
                for s in subdirs:
                    os.makedirs(os.path.join(temp_dir, s.strip(os.path.sep)))
            else:
                raise Exception('subdirs should be tuple or list of strings, '
                                'but currentry subdirs == {}'.format(subdirs))
        return temp_dir

    def get_symlink_to(self, target, temp_dir=None):
        if temp_dir is None:
            temp_dir = self.get_temp_dir()
        linkname = tempfile.mktemp(dir=temp_dir)
        os.symlink(target.strip(os.path.sep), linkname)
        self.logger.debug('Creates temporary symlink "{} -> {}"'
                          ''.format(linkname, target))
        return linkname
