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

import pytest
import sh

from molecule import config
from molecule.dependency import ansible_galaxy


@pytest.fixture
def ansible_galaxy_instance(config_instance):
    return ansible_galaxy.AnsibleGalaxy(config_instance)


def test_config_private_member(ansible_galaxy_instance):
    assert isinstance(ansible_galaxy_instance._config, config.Config)


def test_default_options_property(ansible_galaxy_instance):
    role_file = os.path.join(
        ansible_galaxy_instance._config.scenario.directory, 'requirements.yml')
    roles_path = os.path.join(
        ansible_galaxy_instance._config.ephemeral_directory, 'roles')
    x = {'role_file': role_file, 'roles_path': roles_path, 'force': True}

    assert x == ansible_galaxy_instance.options


def test_name_property(ansible_galaxy_instance):
    assert 'galaxy' == ansible_galaxy_instance.name


def test_enabled_property(ansible_galaxy_instance):
    assert ansible_galaxy_instance.enabled


def test_options_property(ansible_galaxy_instance):
    role_file = os.path.join(
        ansible_galaxy_instance._config.scenario.directory, 'requirements.yml')
    roles_path = os.path.join(
        ansible_galaxy_instance._config.ephemeral_directory, 'roles')
    x = {
        'force': True,
        'role_file': role_file,
        'roles_path': roles_path,
    }

    assert x == ansible_galaxy_instance.options


@pytest.mark.parametrize(
    'config_instance', [{
        'configs': [{
            'dependency': {
                'name': 'galaxy',
                'options': {
                    'foo': 'bar'
                }
            }
        }]
    }],
    indirect=['config_instance'])
def test_options_property_handles_dependency_options(config_instance):
    i = ansible_galaxy.AnsibleGalaxy(config_instance)
    role_file = os.path.join(config_instance.scenario.directory,
                             'requirements.yml')
    roles_path = os.path.join(config_instance.ephemeral_directory, 'roles')
    x = {
        'role_file': role_file,
        'roles_path': roles_path,
        'foo': 'bar',
        'force': True
    }

    assert x == i.options


@pytest.mark.parametrize(
    'config_instance', [{
        'args': {
            'debug': True
        },
    }],
    indirect=['config_instance'])
def test_options_property_handles_cli_args(config_instance):
    i = ansible_galaxy.AnsibleGalaxy(config_instance)
    role_file = os.path.join(config_instance.scenario.directory,
                             'requirements.yml')
    roles_path = os.path.join(config_instance.ephemeral_directory, 'roles')
    x = {
        'force': True,
        'role_file': role_file,
        'roles_path': roles_path,
    }

    # Does nothing.  The `ansible-galaxy` command does not support
    # a `debug` flag.
    assert x == i.options


# The bake command is passed options through kwargs expansion.
# Since dicts are unordered, difficult to assert in a sane way.
def test_bake(ansible_galaxy_instance):
    ansible_galaxy_instance.bake()
    role_file = os.path.join(
        ansible_galaxy_instance._config.scenario.directory, 'requirements.yml')
    roles_path = os.path.join(
        ansible_galaxy_instance._config.ephemeral_directory, 'roles')
    command = str(ansible_galaxy_instance._ansible_galaxy_command).split()

    assert str(sh.ansible_galaxy) == command.pop(0)
    assert 'install' == command.pop(0)
    x = [
        '--force', '--role-file={}'.format(role_file),
        '--roles-path={}'.format(roles_path)
    ]
    assert x == sorted(command)


def test_execute(patched_run_command, ansible_galaxy_instance):
    ansible_galaxy_instance._ansible_galaxy_command = 'patched-command'
    ansible_galaxy_instance.execute()

    role_directory = os.path.join(
        ansible_galaxy_instance._config.scenario.directory,
        ansible_galaxy_instance.options['roles_path'])
    assert os.path.isdir(role_directory)

    patched_run_command.assert_called_once_with('patched-command', debug=None)


def test_execute_does_not_execute(patched_run_command,
                                  ansible_galaxy_instance):
    ansible_galaxy_instance._config.config['dependency']['enabled'] = False
    ansible_galaxy_instance.execute()

    assert not patched_run_command.called


# The bake command is passed options through kwargs expansion.
# Since dicts are unordered, difficult to assert in a sane way.
def test_execute_bakes(patched_run_command, ansible_galaxy_instance):
    ansible_galaxy_instance.execute()
    role_file = os.path.join(
        ansible_galaxy_instance._config.scenario.directory, 'requirements.yml')
    roles_path = os.path.join(
        ansible_galaxy_instance._config.ephemeral_directory, 'roles')
    assert ansible_galaxy_instance._ansible_galaxy_command is not None

    command = str(patched_run_command.call_args[0][0]).split()
    assert str(sh.ansible_galaxy) == command.pop(0)
    assert 'install' == command.pop(0)
    x = [
        '--force', '--role-file={}'.format(role_file),
        '--roles-path={}'.format(roles_path)
    ]
    assert x == sorted(command)
    assert {'debug': None} == patched_run_command.call_args[1]


def test_executes_catches_and_exits_return_code(patched_run_command,
                                                ansible_galaxy_instance):
    patched_run_command.side_effect = sh.ErrorReturnCode_1(sh.ansible_galaxy,
                                                           None, None)
    with pytest.raises(SystemExit) as e:
        ansible_galaxy_instance.execute()

    assert 1 == e.value.code


def test_role_setup(ansible_galaxy_instance):
    role_directory = os.path.join(
        ansible_galaxy_instance._config.scenario.directory,
        ansible_galaxy_instance.options['roles_path'])
    assert not os.path.isdir(role_directory)

    ansible_galaxy_instance._role_setup()

    assert os.path.isdir(role_directory)
