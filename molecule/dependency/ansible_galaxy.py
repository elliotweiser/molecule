#  Copyright (c) 2015-2016 Cisco Systems, Inc.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import os

import sh

from molecule import util
from molecule.dependency import base


class AnsibleGalaxy(base.Base):
    def __init__(self, config):
        """
        Sets up the requirements to execute `ansible-galaxy` and returns None.

        :param config: An instance of a Molecule config.
        :return: None
        """
        super(AnsibleGalaxy, self).__init__(config)
        self._ansible_galaxy_command = None

    @property
    def default_options(self):
        role_file = os.path.join(self._config.scenario.directory,
                                 'requirements.yml')
        roles_path = os.path.join(self._config.ephemeral_directory, 'roles')
        return {
            'force': True,
            'role_file': role_file,
            'roles_path': roles_path
        }

    def bake(self):
        """
        Bake an `ansible-galaxy` command so it's ready to execute and returns
        None.

        :return: None
        """
        self._ansible_galaxy_command = sh.ansible_galaxy.bake(
            'install',
            _env=os.environ,
            _out=util.callback_info,
            _err=util.callback_error,
            **self.options)

    def execute(self):
        """
        Executes `ansible-galaxy` and returns None.

        :return: None
        """
        if not self.enabled:
            return

        if self._ansible_galaxy_command is None:
            self.bake()

        self._role_setup()
        try:
            util.run_command(
                self._ansible_galaxy_command,
                debug=self._config.args.get('debug'))
        except sh.ErrorReturnCode as e:
            util.sysexit(e.exit_code)

    def _role_setup(self):
        role_directory = os.path.join(self._config.scenario.directory,
                                      self.options['roles_path'])
        if not os.path.isdir(role_directory):
            os.makedirs(role_directory)
