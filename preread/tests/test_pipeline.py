"""Offline regression checks for the migrated repository pipeline."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PREREAD = Path(__file__).resolve().parents[1]
REPOSITORY = PREREAD.parent


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, PREREAD / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_script('check_preread')
resolver = load_script('resolve_session')


class ContentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.file = self.root / 'batch' / 'module' / 'lecture' / 'pre-read.md'
        self.file.parent.mkdir(parents=True)
        self.original = (PREREAD / 'tests/fixtures/probability-distributions.md').read_text()
        self.file.write_text(self.original)

    def result(self, text=None, setup=False, setup_text=None):
        if text is not None:
            self.file.write_text(text)
        return checker.check(self.file, setup, self.root, setup_text)

    def test_pack_example_passes_deterministic_checks_but_not_rendered(self):
        result = self.result()
        self.assertTrue(result['ok'], result['findings'])
        self.assertEqual(result['mermaid_render'], 'not-rendered')
        self.assertIn('Beginner readability', result['manual_checks_required'])

    def test_missing_section_and_wrong_setup_fail(self):
        self.assertFalse(self.result(self.original.replace('Mental Map', 'Map'))['ok'])
        self.assertFalse(self.result(self.original, setup=True)['ok'])

    def test_repeated_verb_and_vague_prose_fail(self):
        repeated = self.original.replace('**Determine**', '**Calculate**')
        self.assertIn('Repeated outcome verb', self.result(repeated)['findings'])
        result = self.result(self.original + '\nThis is useful.\n')
        self.assertTrue(any('Vague words:' in finding for finding in result['findings']))

    def test_required_title_is_not_rewritten_for_a_banned_adjective(self):
        text = self.original.replace('## <span style="color:#2F7DDE">Probability Distributions</span>',
                                     '## <span style="color:#2F7DDE">Advanced Probability Distributions</span>')
        self.assertTrue(self.result(text)['ok'])

    def test_recursive_scenario_check_recognizes_both_names(self):
        for name in ('preread.md', 'pre-read.md'):
            other = self.root / 'other-batch' / 'module' / name
            other.parent.mkdir(parents=True, exist_ok=True)
            other.write_text(self.original)
            result = self.result()
            self.assertTrue(any('Exact scenario reuse' in f for f in result['findings']))
            other.unlink()
        scaffold = self.root / 'other-batch' / 'pre-read.md'
        scaffold.write_text('Status: scaffold\n' + self.original)
        self.assertTrue(self.result()['ok'])

    def test_literal_setup_text_and_grammar_edits_are_handled_explicitly(self):
        setup_text = 'This modern tool is useful.'
        section = '\n---\n\n### <span style="color:#2F7DDE">Set Up Before the Session</span>\n\n> ' + setup_text + '\n'
        exact = self.result(self.original + section, setup=True, setup_text=setup_text)
        self.assertTrue(exact['ok'], exact['findings'])
        self.assertTrue(exact['setup_input_exact_match'])
        edited = self.result(self.original + section.replace(setup_text, 'This modern tool feels useful.'), setup=True, setup_text=setup_text)
        self.assertTrue(edited['ok'], edited['findings'])
        self.assertFalse(edited['setup_input_exact_match'])
        self.assertTrue(any('grammar-only' in item for item in edited['manual_checks_required']))

    def test_cli_failures_exit_nonzero(self):
        self.file.write_text('# unfinished\n')
        result = subprocess.run([sys.executable, '-I', str(PREREAD / 'scripts/check_preread.py'),
                                 '--file', str(self.file), '--setup', 'No', '--root', str(self.root)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)['ok'])


class RoutingChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = {'batches': [{'batch': 'AIML', 'modules': [
            {'module_id': '08', 'title': 'Generative AI', 'sessions': [
                {'source_session': '27.1', 'title': 'Agents', 'path': 'AIML/module-08/lecture-27.1-agents'}]},
            {'module_id': 'capstone', 'title': 'Capstone', 'sessions': [
                {'source_session': '27.1', 'title': 'Capstone', 'path': 'AIML/module-capstone/lecture-27.1-capstone'}]}
        ]}]}
        self.save()

    def save(self):
        (self.root / 'curriculum-index.json').write_text(json.dumps(self.index))

    def test_duplicate_source_session_requires_module(self):
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            resolver.resolve(self.root, 'AIML', '27.1')
        result = resolver.resolve(self.root, 'AIML', '27.1', '08')
        self.assertEqual(Path(result['output_path']).name, 'pre-read.md')
        self.assertIn('module-08', result['output_path'])

    def test_unknown_session_and_path_escape_are_rejected(self):
        with self.assertRaises(ValueError):
            resolver.resolve(self.root, 'AIML', '99.1')
        self.index['batches'][0]['modules'][0]['sessions'][0]['path'] = '../outside'
        self.save()
        with self.assertRaisesRegex(ValueError, 'escapes'):
            resolver.resolve(self.root, 'AIML', '27.1', '08')

    def test_actual_repository_session_11_1_resolves(self):
        if not (REPOSITORY / 'curriculum-index.json').exists():
            self.skipTest('Repository baseline is still materializing')
        result = resolver.resolve(REPOSITORY, 'IITREICT-AIML-EN-II-2608', '11.1')
        self.assertEqual(result['session_name'], 'Cleaning Data I: Missing Values and Duplicates')
        self.assertTrue(Path(result['output_path']).is_file())


class RegistrationChecks(unittest.TestCase):
    def test_agent_registration_uses_only_supported_string_fields(self):
        for filename in ('agent_preread_creator', 'agent_preread_verifier'):
            path = REPOSITORY / '.codex/agents' / (filename + '.toml')
            # The registration uses only one-line TOML basic strings, a JSON-compatible subset.
            values = {}
            for line in path.read_text().splitlines():
                key, value = line.split('=', 1)
                values[key.strip()] = json.loads(value.strip())
            self.assertEqual(set(values), {'name', 'description', 'developer_instructions'})
            self.assertEqual(values['name'], filename)
            self.assertTrue(all(isinstance(v, str) and v for v in values.values()))
            self.assertNotIn('claude', values['developer_instructions'].lower())


if __name__ == '__main__':
    unittest.main()
