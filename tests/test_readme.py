import os
import shlex
import subprocess
import unittest


README_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')


class TestReadMe(unittest.TestCase):
    def _find_code_blocks(self, fobj):
        inside_block = False
        command = None
        output_lines = []
        for line in fobj:
            if not inside_block and line.strip() == '```':
                inside_block = True
            elif inside_block and line.strip() == '```':
                if command is not None:
                    yield (command, ''.join(output_lines))
                output_lines.clear()
                command = None
                inside_block = False
            elif line.lstrip().startswith('$'):
                if command is not None:
                    yield (command, ''.join(output_lines))
                    output_lines.clear()
                command = line.lstrip()[1:]
            elif inside_block:
                output_lines.append(line)
        if command is not None:
            yield (command, ''.join(output_lines))

    def _check_code_block(self, command, expected_output):
        got = subprocess.check_output(shlex.split(command), stderr=subprocess.STDOUT)
        self.assertEqual(expected_output, got.decode('utf-8'))

    def test_readme(self):
        with open(README_FILE) as readme:
            for command, output in self._find_code_blocks(readme):
                self._check_code_block(command, output)