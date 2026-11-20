#!/usr/bin/env python3
"""Check deterministic pre-read rules; do not execute document code."""
import argparse
import ast
import json
import re
from pathlib import Path

BANKS = [
    'name list recall identify',
    'classify explain describe interpret summarise predict',
    'calculate determine solve use apply estimate demonstrate',
    'compare differentiate trace examine',
    'judge justify check critique',
    'design build write plan',
]
LEVEL = {word: level for level, words in enumerate(BANKS) for word in words.split()}
FORBIDDEN = r'\b(?:leverage|utilize|robust|seamlessly|empower|cutting-edge|dive into|delve|learning objectives?|LO|compute)\b'
VAGUE = r'\b(?:various|several|many|some|things|stuff|etc|basically|simply|easily|just|really|very|a lot|kind of|powerful|efficient|modern|advanced|better|good|great|nice|handy|useful)\b'
SECTIONS = ['Mental Map', "What You'll Learn", 'Why You Are Learning This Topic',
            'Puzzle', 'Think It Through', 'One Question to Carry Into the Session']


def plain(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', text)
    return re.sub(r'[#>*`|\[\]]', '', text)


def scenario_from(text):
    match = re.search(r'Real-world example</b><br/>(.*?)"\]', text, re.S)
    return plain(match.group(1)).strip() if match else None


def check(path, setup, root, setup_text=None):
    content = path.read_text()
    findings = []
    code_syntax = []
    setup_notes = []
    setup_input_match = None
    def require(condition, message):
        if not condition:
            findings.append(message)
    body = re.sub(r'```.*?```', '', content, flags=re.S)
    headings = [plain(h).strip() for h in re.findall(r'^### (.*)', content, re.M)]
    expected = SECTIONS + (['Set Up Before the Session'] if setup else [])
    normalized = ['Puzzle' if h.endswith(' Puzzle') else h for h in headings]
    require(normalized == expected, 'Headings are missing, added, or out of order')
    require(len(re.findall(r'^## (?!#)', content, re.M)) == 1, 'Use exactly one H2 session title')
    require(('Set Up Before the Session' in headings) == setup, 'Setup section does not match the supplied flag')
    require(not any(marker in body for marker in (':::', '{{', '[paste', '<!--')), 'Unfilled placeholder or unsupported callout')
    require(not re.search(r'\{[^}\n]+\}', body), 'Unfilled brace placeholder')
    # Immutable user-supplied labels are not authored explanatory prose.
    prose = re.sub(r'^## (?!#).*$', '', body, flags=re.M)
    prose = re.sub(r'^>[^\n]*Topics you will meet:[^\n]*$', '', prose, flags=re.M)
    prose = re.sub(r'(?:A |An )?(?:<span[^>]*>)?\*\*[^*]+\*\*(?:</span>)?(?= means)', '', prose)
    if setup_text:
        setup_section = re.search(r'(### [^\n]*Set Up Before the Session[^\n]*\n)(.*)', prose, re.S)
        if setup_section:
            start = setup_section.start(2)
            prose = prose[:start] + prose[start:].replace(setup_text, '')
        setup_input_match = setup_text in sections_setup_text(content)
        if not setup_input_match:
            setup_notes.append('Setup text differs from input: verify grammar-only edits, unchanged URLs, and setup prose vocabulary manually')
            # Semantic equivalence of an allowed grammar edit cannot be certified by string matching.
            prose = re.sub(r'(### [^\n]*Set Up Before the Session[^\n]*\n).*', r'\1', prose, flags=re.S)
    forbidden = sorted(set(re.findall(FORBIDDEN, prose, re.I)))
    vague = sorted(set(re.findall(VAGUE, prose, re.I)))
    require(not forbidden, 'Forbidden words: ' + ', '.join(forbidden))
    require(not vague, 'Vague words: ' + ', '.join(vague))
    colors = {c.lower() for c in re.findall(r'#[0-9a-fA-F]{6}\b', body)}
    require(colors <= {'#2f7dde', '#d9660b'}, 'Unsupported text color')
    fences = re.findall(r'^```([^\n]*)\n(.*?)^```[ \t]*$', content, re.M | re.S)
    require(len(re.findall(r'^```', content, re.M)) == 2 * len(fences), 'Unclosed or malformed code fence')
    diagrams = [block for lang, block in fences if lang.strip() == 'mermaid']
    require(len(diagrams) == 1, 'Use exactly one Mermaid block')
    for lang, block in fences:
        lang = lang.strip()
        if lang == 'mermaid':
            continue
        require(lang == 'python', 'Only Python previews are supported')
        require(len(block.rstrip('\n').splitlines()) <= 3, 'Code preview exceeds three lines')
        if lang == 'python':
            try:
                ast.parse(block)
                code_syntax.append('parsed-not-executed')
            except SyntaxError as error:
                code_syntax.append('syntax-error')
                findings.append('Python syntax error: ' + str(error))
    if diagrams:
        diagram = diagrams[0]
        require('flowchart TB' in diagram, 'Mental map must use flowchart TB')
        nodes = re.findall(r'^\s*([A-Za-z_]\w*)\s*\["', diagram, re.M)
        require(len(nodes) == 4 and len(set(nodes)) == 4, 'Mental map must define exactly four boxes')
        require(all(label in diagram for label in ('Current Session', 'The Big Question', 'Course use case', 'Real-world example')), 'Mental map is missing a required box label')
    sections = {}
    matches = list(re.finditer(r'^### (.*)$', content, re.M))
    for i, match in enumerate(matches):
        name = plain(match.group(1)).strip()
        sections[name] = content[match.end():matches[i+1].start() if i+1 < len(matches) else len(content)]
    outcomes = sections.get("What You'll Learn", '')
    require('Have you ever wondered' in outcomes, 'Learning outcomes need the curiosity hook')
    require('By the end of this session, you will be able to:' in outcomes, 'Missing fixed learning-outcome lead-in')
    require('Topics you will meet:' in outcomes and 'Join the session to learn each of these in detail.' in outcomes, 'Missing Topics or Join callout')
    bullets = re.findall(r'^- (.*)$', outcomes, re.M)
    verbs = []
    for bullet in bullets:
        match = re.match(r'<span[^>]*>\*\*([A-Za-z]+)\*\*</span>', bullet)
        require(match is not None, 'Each outcome must start with one colored bold action verb')
        if match:
            verbs.append(match.group(1).lower())
    require(4 <= len(bullets) <= 6, 'Use four to six outcome bullets')
    require(all(v in LEVEL for v in verbs), 'Outcome verb outside Bloom bank')
    require(len(verbs) == len(set(verbs)), 'Repeated outcome verb')
    levels = [LEVEL[v] for v in verbs if v in LEVEL]
    require(levels == sorted(levels), 'Outcome verbs must progress from lower to higher Bloom levels')
    think = sections.get('Think It Through', '')
    numbers = re.findall(r'^\*\*(\d)\.', think, re.M)
    require(numbers == ['1', '2', '3'], 'Think It Through must have exactly three numbered questions')
    require(len(re.findall(r'^Hint:', think, re.M)) == 3, 'Think It Through must have three one-line hints')
    text = plain(body)
    sentence_text = plain(prose)
    sentences = [s.strip() for s in re.split(r'(?<=[.?!])\s+|\n+', sentence_text) if s.strip()]
    long_sentences = [s for s in sentences if len(s.split()) > 20]
    require(not long_sentences, 'Sentences or prose lines exceed twenty words')
    word_count = len(text.split())
    require(300 <= word_count <= 500, 'Body word count outside the target 300–500 range')
    scenario = scenario_from(content)
    require(bool(scenario), 'Cannot locate the Real-world example scenario')
    prior = []
    for candidate in sorted(root.rglob('*.md')):
        if candidate.name not in ('pre-read.md', 'preread.md') or candidate.resolve() == path.resolve():
            continue
        if any(part.startswith('.') for part in candidate.relative_to(root).parts):
            continue
        previous = candidate.read_text()
        if 'Status: scaffold' in previous or '{SESSION_NAME}' in previous:
            continue
        other = scenario_from(previous)
        if other:
            prior.append({'file': str(candidate.relative_to(root)), 'scenario': other})
            if scenario and re.sub(r'\W+', ' ', scenario).lower().strip() == re.sub(r'\W+', ' ', other).lower().strip():
                findings.append('Exact scenario reuse: ' + str(candidate.relative_to(root)))
    return {'ok': not findings, 'findings': findings, 'body_words': word_count,
            'outcome_verbs': verbs, 'think_questions': len(numbers), 'scenario': scenario,
            'prior_scenarios': prior, 'code_preview_syntax': code_syntax,
            'mermaid_render': 'not-rendered', 'setup_input_exact_match': setup_input_match,
            'manual_checks_required': ['Topic and objective coverage', 'Scenario originality beyond exact text',
                                       'Beginner readability', 'No answers leaked', 'Snippet execution', 'Mermaid rendering'] + setup_notes}


def sections_setup_text(content):
    match = re.search(r'^### [^\n]*Set Up Before the Session[^\n]*\n(.*)', content, re.M | re.S)
    return match.group(1) if match else ''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--setup', required=True, choices=['Yes', 'No'])
    parser.add_argument('--root', default='.', type=Path)
    parser.add_argument('--setup-text', help='Exact literal setup text supplied by the user')
    args = parser.parse_args()
    try:
        result = check(args.file.resolve(), args.setup == 'Yes', args.root.resolve(), args.setup_text)
    except (OSError, ValueError) as error:
        result = {'ok': False, 'findings': [str(error)]}
    print(json.dumps(result, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
