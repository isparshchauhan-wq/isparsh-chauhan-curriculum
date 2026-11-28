#!/usr/bin/env python3
"""Deterministic checker for a lecture script (format v2).

Usage:
    python3 check_script.py <lecture_script.md> [--los "LO 1;LO 2;..."] [--announcements yes|no]
                            [--module "Module name"] [--session "Session name"] [--duration 90|120]

Exit code 0 = no FAIL. Prints one line per finding: FAIL (must fix) or WARN (look at it).
It checks structure, numbers and wording rules only. It cannot judge accuracy; the verifier does that.
"""
import json, os, re, sys

BANNED = [  # (label, regex, apply_to_code)
    ("synthetic", r"(?i)\bsynthetic\b"),
    ("facilitator", r"(?i)\bfacilitator"),
    ("I Do / We Do / You Do", r"\b(I|We|You) Do\b"),
    ("Recap", r"(?i)\brecap\b"),
    ("Break", r"\bBreak\b"),
    ("Time plan", r"(?i)\btime plan\b"),
    ("[Script:]", r"\[Script:"),
    ("Spine", r"(?i)\bspine\b"),
    ("Exit Ticket", r"(?i)\bexit ticket"),
    ("Appendix", r"(?i)\bappendix\b"),
    ("Connects To", r"(?i)\bconnects to\b"),
    ("Builds on", r"(?i)\bbuilds on\b"),
    ("Format: line", r"(?m)^\**Format:"),
    ("Step N (lecture part)", r"\bSteps? \d\b"),
    ("unfilled placeholder", r"\{\{\s*[A-Za-z_]"),
]
ORDER = ["Agenda", "Scenario", "Problem Statement", "What We Will Use", "How:",
         "Topic 1:", "Topic 2:", "Topic 3:", "Topic 4:", "Closing: Outcome & Summary"]


def is_emoji(ch):
    o = ord(ch)
    if ch == "\U0001F3AF":
        return False
    return (0x1F300 <= o <= 0x1FAFF) or (0x2600 <= o <= 0x27BF) or (0x2B00 <= o <= 0x2BFF) or o == 0xFE0F


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    path = argv[1]
    opt = {}
    i = 2
    while i < len(argv):
        if argv[i].startswith("--") and i + 1 < len(argv):
            opt[argv[i][2:]] = argv[i + 1]
            i += 2
        else:
            i += 1
    try:
        duration = int(opt.get("duration", "120"))
        if duration not in (90, 120):
            raise ValueError()
    except ValueError:
        print("FAIL --duration must be 90 or 120")
        return 1
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    lines = text.split("\n")
    base = os.path.dirname(os.path.abspath(path))
    out = []

    def fail(m): out.append("FAIL " + m)
    def warn(m): out.append("WARN " + m)

    # split prose and code
    prose, blocks, cur, in_code, lang, start = [], [], [], False, "", 0
    for n, ln in enumerate(lines, 1):
        if ln.startswith("```"):
            if not in_code:
                in_code, lang, cur, start = True, ln[3:].strip(), [], n
            else:
                blocks.append((lang, cur, start, n))
                in_code = False
            continue
        if in_code:
            cur.append(ln)
        else:
            prose.append((n, ln))
    if in_code:
        fail(f"unclosed code fence starting at line {start}")

    # headings and order
    heads = [(n, re.sub(r"<[^>]+>", "", ln).lstrip("# ").strip()) for n, ln in prose if re.match(r"^##\s", ln)]
    pos = []
    for key in ORDER:
        hit = [n for n, h in heads if h.startswith(key)]
        if len(hit) != 1:
            fail(f"section '{key}' found {len(hit)} times (need exactly 1)")
            pos.append(None)
        else:
            pos.append(hit[0])
    seq = [p for p in pos if p]
    if seq != sorted(seq):
        fail("sections are out of order: " + ", ".join(ORDER))
    ann = [n for n, h in heads if h.startswith("Announcements")]
    poll = [n for n, ln in prose if re.match(r"^#\s", ln) and "Launch the Feedback Poll" in ln]
    if len(poll) != 1:
        fail("the red H1 'Launch the Feedback Poll' must appear once")
    want = opt.get("announcements", "").lower()
    if want == "yes" and len(ann) != 1:
        fail("Announcements = Yes but the Announcements section is missing")
    if want == "no" and ann:
        fail("Announcements = No but the Announcements section is present")
    if poll and pos[-1] and poll[0] < pos[-1]:
        fail("Feedback Poll must come after the Closing")
    if poll and ann and poll[0] < ann[0]:
        fail("Feedback Poll must come after Announcements")
    if poll and any(n > poll[0] for n, h in heads):
        fail("No teaching section may follow the Feedback Poll")
    if ann and pos[-1] and ann[0] < pos[-1]:
        fail("Announcements must come after the Closing")
    topic_heads = [h for n, h in heads if re.match(r"Topic \d", h)]
    if len(topic_heads) != 4:
        fail(f"need exactly 4 Topic sections, found {len(topic_heads)}")
    for n, h in heads:
        if re.match(r"(Step|Block|Part) \d", h):
            fail(f"line {n}: use 'Topic N', not '{h[:20]}'")

    # Restrict pacing rows to the Agenda.
    minutes = []
    agenda_rows = [(n, ln) for n, ln in prose if pos[0] and pos[1] and pos[0] < n < pos[1]]
    for n, ln in agenda_rows:
        m = re.match(r"^\|\s*(\d|—)\s*\|(.*)\|\s*(\d+)\s*\|\s*$", ln)
        if m:
            minutes.append(int(m.group(3)))
    if len(minutes) != 5:
        fail(f"Agenda should have 4 topic rows and a Closing row with minutes; found {len(minutes)}")
    elif sum(minutes) != duration:
        fail(f"Agenda minutes add up to {sum(minutes)}, not {duration}")
    if not any(f"**{duration}**" in ln for _, ln in agenda_rows):
        fail(f"Agenda needs a Total row with **{duration}**")
    head_min = []
    for n, ln in prose:
        if re.match(r"^##\s.*(Topic \d|Closing: Outcome)", ln):
            m = re.search(r"`(\d+) min`", ln)
            head_min.append(int(m.group(1)) if m else None)
    if len(minutes) == 5 and head_min and head_min != minutes:
        fail(f"heading minutes {head_min} do not match Agenda minutes {minutes}")

    agenda_txt = ""
    if pos[0] and pos[1]:
        agenda_txt = "\n".join(lines[pos[0]:pos[1] - 1])
    if "los" in opt or "los-json" in opt:
        try:
            expected = json.loads(opt["los-json"]) if "los-json" in opt else opt["los"].split(";")
            if not isinstance(expected, list) or any(not isinstance(lo, str) for lo in expected):
                raise ValueError()
        except ValueError:
            print("FAIL --los-json expects a JSON array of strings")
            return 1
        agenda_los = []
        for row in agenda_txt.splitlines():
            cells = re.split(r"(?<!\\)\|", row)
            if len(cells) >= 5 and cells[1].strip() in ("1", "2", "3", "4"):
                agenda_los.extend(x.strip().replace(r"\|", "|") for x in re.split(r"<br\s*/?>", cells[3]))
        for lo in [lo.strip() for lo in expected if lo.strip()]:
            count = agenda_los.count(lo)
            if count != 1:
                fail(f"LO not verbatim exactly once in the Agenda ({count} times): {lo[:70]}")

    # quizzes
    qpos = [n for n, ln in prose if re.match(r"^###\s.*Quiz \d", ln)]
    if len(qpos) != 4:
        fail(f"need exactly 4 quizzes, found {len(qpos)}")
    for qi, q in enumerate(qpos):
        end = qpos[qi + 1] if qi + 1 < len(qpos) else len(lines)
        seg = "\n".join(lines[q:min(end, q + 40)])
        if not re.search(r"\*\*Question:\*\*", seg): fail(f"Quiz {qi+1}: no **Question:**")
        if sorted(re.findall(r"^- ([A-D])\) ", seg, re.M)) != list("ABCD"): fail(f"Quiz {qi+1}: needs unique options A to D")
        if not re.search(r"\*\*Correct Answer:\*\* [A-D]\b", seg): fail(f"Quiz {qi+1}: no **Correct Answer:** letter")
        if sorted(re.findall(r"^- \*\*([A-D])\)\*\*", seg, re.M)) != list("ABCD"): fail(f"Quiz {qi+1}: needs one explanation for each option A to D")
    if len(qpos) == 4 and len(topic_heads) == 4:
        tp = [n for n, h in heads if re.match(r"Topic \d", h)]
        tp.append(pos[-1] or len(lines))
        for k in range(4):
            c = sum(1 for q in qpos if tp[k] < q < tp[k + 1])
            if c != 1:
                fail(f"Topic {k+1} contains {c} quizzes (need 1)")
    for n, ln in prose:
        if re.match(r"^#{3,4}\s.*>(Why|What|How)<", ln):
            fail(f"line {n}: no per-topic Why/What/How headings")

    # banned terms (prose and code), module and emoji
    for n, ln in enumerate(lines, 1):
        for label, rx in BANNED:
            if re.search(rx, ln):
                fail(f"line {n}: banned term '{label}'")
        for ch in ln:
            if is_emoji(ch):
                fail(f"line {n}: emoji {ch!r} (only the target emoji is allowed)")
                break
    module_pattern = r"(?<!\w)" + re.escape(opt.get("module", "")) + r"(?!\w)"
    prose_text = "\n".join(ln for _, ln in prose)
    prose_text = re.sub(r"\[[^\]]+\]\([^)]*\)", "", prose_text)
    if opt.get("module") and re.search(module_pattern, prose_text, re.I):
        fail("the Module Name must never be printed")
    if opt.get("session") and opt["session"].lower() not in lines[0].lower():
        warn("title line does not contain the session name")

    # instructor notes: 1-2 lines
    i = 0
    while i < len(lines):
        if "Instructor Note" in lines[i] and lines[i].startswith(">"):
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                j += 1
            if j - i > 2:
                fail(f"line {i+1}: Instructor Note is {j-i} lines (max 2)")
            i = j
        else:
            i += 1

    # code blocks
    n_code = 0
    for lang, body, s, e in blocks:
        if lang in ("python", "sql", "py", "r", "bash"):
            n_code += 1
            if len(body) > 10:
                fail(f"line {s}: {lang} block has {len(body)} lines (max 10)")
            nxt = "\n".join(lines[e:e + 4])
            if "**Output**" not in nxt:
                fail(f"line {s}: {lang} block is not followed by **Output**")
    for n, ln in prose:
        if ln.strip() == "**Output**":
            pass
    if n_code == 0:
        warn("no code blocks (fine for a no-code session)")
    for n, ln in prose:
        if "Code Explanation" in ln or "Logic Explanation" in ln:
            break
    else:
        if n_code:
            fail("no Code Explanation heading found")

    # images
    from pathlib import Path
    for n, ln in prose:
        for m in re.finditer(r'<img\s+[^>]*>', ln):
            tag = m.group(0)
            src = re.search(r'src="([^"]+)"', tag)
            if src and not (Path(base) / src.group(1)).resolve().is_relative_to(Path(base)):
                fail(f"line {n}: image path must remain inside the lecture directory")
            if not src or not os.path.isfile(os.path.join(base, src.group(1))):
                fail(f"line {n}: image missing: {src.group(1) if src else tag[:40]}")
            if 'alt="' not in tag: fail(f"line {n}: image has no alt text")
            if 'width="900"' not in tag: fail(f"line {n}: image should use width=\"900\"")
    if re.search(r"!\[", text):
        fail("use <img ... width=\"900\"> instead of markdown images")

    # Check required pieces inside the Closing.
    close_end = min(ann + poll + [len(lines) + 1])
    closing_text = "\n".join(lines[pos[-1]:close_end - 1]) if pos[-1] else ""
    for needle in ("Outcome", "Summary", "Therefore"):
        if needle not in closing_text:
            fail(f"Closing needs '{needle}'")
    if "30 seconds to respond in chat" not in text:
        warn("no 'Give learners 30 seconds to respond in chat.' prompt found")
    if "Practical value" not in closing_text:
        fail("Summary needs a 'Practical value' row")

    for m in out:
        print(m)
    nf = sum(1 for m in out if m.startswith("FAIL"))
    print(f"\n{'PASS' if nf == 0 else 'FAIL'}: {nf} fail, {len(out) - nf} warn  ({path})")
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
