from collections import namedtuple

try:
    from unittest import TestCase
    from unittest.mock import patch
except ImportError:
    from mock import patch

from click.testing import CliRunner

from sagify.__main__ import cli

Case = namedtuple('Case', 'description, init_cmd, push_cmd, expected_exit_code, expected_cli_call')

t1 = Case('sagify push', ['init'], ['push'], 0,
          lambda command_line: command_line.assert_called_once_with(['sagify/push.sh', 'latest', None, None, None]))

t2 = Case('sagify push -p profile', ['init'], ['push', '-p', 'some-profile'], 0,
          lambda command_line: command_line.assert_called_once_with(['sagify/push.sh', 'latest', None, None, 'some-profile']))

t3 = Case('sagify push -r region', ['init'], ['push', '-r', 'some-region'], 0,
          lambda command_line: command_line.assert_called_once_with(['sagify/push.sh', 'latest', 'some-region', None, None]))

t4 = Case('sagify push -r region -p profile', ['init'], ['push', '-r', 'some-region', '-p', 'prof'], 0,
          lambda command_line: command_line.assert_called_once_with(['sagify/push.sh', 'latest', 'some-region', None, 'prof']))

t5 = Case('sagify push -d dir/', ['init', '-d', 'src/'], ['push', '-d', 'src/'], 0,
          lambda command_line: command_line.assert_called_once_with(['src/sagify/push.sh', 'latest', None, None, None]))

t6 = Case('sagify push -d invalid_dir/', ['init', '-d', 'src/'], ['push', '-d', 'invalid_dir/'], -1,
          lambda command_line: command_line.assert_not_called())

t7 = Case('sagify push -i aws-role', ['init'], ['push', '-i', 'some-role-arn'], 0,
          lambda command_line: command_line.assert_called_once_with(['sagify/push.sh', 'latest', None, 'some-role-arn', None]))

t8 = Case('sagify -p profile -i aws-role', ['init'], ['push', '-i', 'some-role-arn', '-p', 'some-profile'], 2,
          lambda command_line: command_line.assert_not_called())

test_cases = [t1, t2, t3, t4, t5, t6, t7, t8]

# Mocks
command_line_mock = patch('future.moves.subprocess.check_output', return_value=None)
patch('sagify.commands.initialize._get_local_aws_profiles', return_value=['default', 'sagemaker']).start()


class PushCommandTests(TestCase):

    def tests(self):
        for case in test_cases:
            command_line = command_line_mock.start()

            try:
                assert runCommands(case.init_cmd, case.push_cmd).exit_code == case.expected_exit_code
                case.expected_cli_call(command_line)
            except AssertionError as e:
                e.args = ('Test Case: {}'.format(case.description), e.args)
                raise

            command_line.stop()


def runCommands(init_command, push_command):
    runner = CliRunner()
    with runner.isolated_filesystem():
        runner.invoke(cli=cli, args=init_command, input='my_app\n1\n2\nus-east-1\n')
        return runner.invoke(cli=cli, args=push_command)
