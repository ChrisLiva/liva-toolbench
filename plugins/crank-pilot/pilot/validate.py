"""Shape checks for an interaction file, and the one containment check for a file named inside an effort directory."""

import re
from pathlib import Path

KINDS = ("questions", "readback", "prototype")
PHASES = ("brainstorm", "spec", "plan")


def inside(root: Path, rel: str) -> Path | None:
    """The resolved path of `rel` when it is relative, stays within `root`, and names a regular file, else None."""
    if not isinstance(rel, str) or not rel or Path(rel).is_absolute():
        return None
    try:
        base = root.resolve()
        target = (base / rel).resolve()
        return target if target.is_relative_to(base) and target.is_file() else None
    except (OSError, ValueError, RuntimeError):
        return None


def _strings(data: dict, names: tuple[str, ...], path: str) -> list[str]:
    problems = []
    for name in names:
        if name not in data:
            problems.append(f"{path}{name}: required")
        elif not isinstance(data[name], str):
            problems.append(f"{path}{name}: must be a string")
    return problems


def _string_list(data: dict, name: str) -> list[str]:
    if name not in data:
        return [f"{name}: required"]
    value = data[name]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return [f"{name}: must be a list of strings"]
    return []


def _agenda(data: dict) -> list[str]:
    if "agenda" not in data:
        return ["agenda: required"]
    agenda = data["agenda"]
    if not isinstance(agenda, dict):
        return ["agenda: must be an object"]
    problems = []
    for name in ("settled", "open"):
        problems += [f"agenda.{line}" for line in _string_list(agenda, name)]
    return problems + _strings(agenda, ("current",), "agenda.")


def _unique(items: list, path: str, field: str = "id") -> list[str]:
    """One `duplicate` line for each item whose `field` an earlier item of the list already used."""
    seen: set[str] = set()
    problems = []
    for index, item in enumerate(items):
        value = item.get(field) if isinstance(item, dict) else None
        if isinstance(value, str):
            if value in seen:
                problems.append(f"{path}[{index}].{field}: duplicate {value!r}")
            seen.add(value)
    return problems


def _question(question: object, path: str) -> list[str]:
    if not isinstance(question, dict):
        return [f"{path}: must be an object"]
    problems = _strings(question, ("id", "title", "body", "recommendation"), f"{path}.")
    options = question.get("options")
    recommended = question.get("recommended")
    if "options" in question:
        if not isinstance(options, list) or not options or any(
            not isinstance(o, dict) or not isinstance(o.get("id"), str) or not isinstance(o.get("label"), str)
            for o in options
        ):
            problems.append(f"{path}.options: must be a non-empty list of objects with string id and label")
        else:
            problems += _unique(options, f"{path}.options")
            if not isinstance(recommended, str):
                problems.append(f"{path}.recommended: required when options are given")
            elif recommended not in {o["id"] for o in options}:
                problems.append(f"{path}.recommended: {recommended!r} names no option")
    elif "recommended" in question:
        problems.append(f"{path}.recommended: needs options")
    return problems


def _questions(items: object, path: str, non_empty: bool) -> list[str]:
    if not isinstance(items, list) or (non_empty and not items):
        return [f"{path}: must be {'a non-empty' if non_empty else 'a'} list of questions"]
    problems = []
    for index, question in enumerate(items):
        problems += _question(question, f"{path}[{index}]")
    return problems + _unique(items, path)


def _artifact(data: dict, effort: Path) -> list[str]:
    name = data["artifact"]
    if not isinstance(name, str):
        return ["artifact: must be a string"]
    if inside(effort, name) is None:
        return ["artifact: must be a relative path to an existing file inside the effort directory"]
    if not name.endswith(".md"):
        return ["artifact: must be a .md file"]
    if Path(name).name != name:
        return ["artifact: must be directly in the effort directory, not in a subdirectory"]
    return []


def _readback(data: dict, effort: Path) -> list[str]:
    problems = _artifact(data, effort) if "artifact" in data else ["artifact: required"]
    problems += _strings(data, ("lead",), "")
    for name in ("judgment_calls", "review_landed", "edits"):
        problems += _string_list(data, name)
    if "decisions" in data:
        problems += _questions(data["decisions"], "decisions", non_empty=False)
    else:
        problems.append("decisions: required")
    return problems


def _variant(variant: object, path: str, effort: Path) -> list[str]:
    if not isinstance(variant, dict):
        return [f"{path}: must be an object"]
    problems = _strings(variant, ("key", "name", "file"), f"{path}.")
    if isinstance(variant.get("file"), str) and inside(effort, variant["file"]) is None:
        problems.append(f"{path}.file: must be a relative path to an existing file inside the effort directory")
    return problems


def _prototype(data: dict, effort: Path) -> list[str]:
    problems = _strings(data, ("question",), "")
    variants = data.get("variants")
    if "variants" not in data:
        return problems + ["variants: required"]
    if not isinstance(variants, list) or len(variants) < 2:
        return problems + ["variants: must be a list of at least two variants"]
    for index, variant in enumerate(variants):
        problems += _variant(variant, f"variants[{index}]", effort)
    return problems + _unique(variants, "variants", "key")


def interaction_problems(data: object, effort: Path) -> list[str]:
    """Every way `data` fails the interaction contract, one `<field path>: <problem>` line each; empty when valid."""
    if not isinstance(data, dict):
        return ["interaction: must be a JSON object"]
    problems = []
    kind = data.get("kind")
    if kind not in KINDS:
        problems.append(f"kind: must be one of {', '.join(KINDS)}")
    if data.get("phase") not in PHASES:
        problems.append(f"phase: must be one of {', '.join(PHASES)}")
    problems += _strings(data, ("title",), "") + _agenda(data)
    if kind == "questions":
        problems += _questions(data["questions"], "questions", non_empty=True) if "questions" in data else ["questions: required"]
    elif kind == "readback":
        problems += _readback(data, effort)
    elif kind == "prototype":
        problems += _prototype(data, effort)
    return problems


def _answer(answer: object, question: dict, number: int, effort: Path, path: str) -> list[str]:
    if not isinstance(answer, dict):
        return [f"{path}: must be an object"]
    problems = _strings(answer, ("text", "note"), f"{path}.")
    if not isinstance(answer.get("accepted"), bool):
        problems.append(f"{path}.accepted: must be true or false")
    option, text = answer.get("option"), answer.get("text")
    offered = {o["id"] for o in question.get("options", [])}
    if option is not None and (not isinstance(option, str) or option not in offered):
        problems.append(f"{path}.option: must be null{' or one of ' + ', '.join(sorted(offered)) if offered else ''}")
    elif isinstance(text, str) and isinstance(answer.get("accepted"), bool):
        if offered and option is None and not text:
            problems.append(f"{path}.text: an own answer needs text")
        accepted = option == question.get("recommended") if offered else not text
        if answer["accepted"] != accepted:
            problems.append(f"{path}.accepted: must be {str(accepted).lower()} for this answer")
    return problems + _attachments(answer, number, effort, path)


def _attachments(holder: dict, number: int, effort: Path, path: str) -> list[str]:
    """The `attachments` list of an answer or a mark: paths of images stored for interaction `number`."""
    attachments = holder.get("attachments")
    if not isinstance(attachments, list) or any(not isinstance(a, str) for a in attachments):
        return [f"{path}.attachments: must be a list of paths"]
    ours = re.compile(rf"pilot/attachments/{number:03d}-\d+\.(png|jpe?g|gif|webp)")
    return [f"{path}.attachments[{index}]: not an image stored for this interaction"
            for index, name in enumerate(attachments) if not ours.fullmatch(name) or inside(effort, name) is None]


def _answers(body: dict, asked: list[dict], number: int, effort: Path) -> list[str]:
    """The answers of a question round, or of a readback's open decisions: one valid answer for each question asked."""
    answers = body.get("answers")
    if not isinstance(answers, list):
        return ["answers: required, a list"]
    questions = {q["id"]: q for q in asked}
    problems = _unique(answers, "answers")
    for index, answer in enumerate(answers):
        name = answer.get("id") if isinstance(answer, dict) else None
        known = questions.get(name) if isinstance(name, str) else None
        if known is None:
            problems.append(f"answers[{index}].id: names no question of this interaction")
        else:
            problems += _answer(answer, known, number, effort, f"answers[{index}]")
    answered = {a["id"] for a in answers if isinstance(a, dict) and isinstance(a.get("id"), str)}
    return problems + [f"answers: no answer for {qid!r}" for qid in questions if qid not in answered]


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _anchor(mark: dict, lines: int, path: str) -> list[str]:
    """The quote, source lines, heading, and occurrence a comment or a strike carries, in a version of `lines` lines."""
    problems = []
    if not isinstance(mark.get("quote"), str) or not mark["quote"]:
        problems.append(f"{path}.quote: must be the non-empty selected text")
    span = mark.get("lines")
    if not (isinstance(span, list) and len(span) == 2 and all(_integer(n) for n in span) and 1 <= span[0] <= span[1] <= lines):
        problems.append(f"{path}.lines: must be [first, last] within 1 and {lines}, first not after last")
    if not isinstance(mark.get("heading"), str):
        problems.append(f"{path}.heading: must be a string")
    if not _integer(mark.get("occurrence")) or mark["occurrence"] < 1:
        problems.append(f"{path}.occurrence: must be an integer from 1")
    return problems


def _mark(mark: object, expected: int, lines: int, number: int, effort: Path, path: str) -> list[str]:
    if not isinstance(mark, dict):
        return [f"{path}: must be an object"]
    problems = [] if mark.get("n") == expected and _integer(mark["n"]) else [f"{path}.n: must be {expected}"]
    kind = mark.get("type")
    if kind not in ("comment", "strike", "note"):
        return problems + [f"{path}.type: must be one of comment, strike, note"]
    if not isinstance(mark.get("text"), str):
        problems.append(f"{path}.text: must be a string")
    elif not mark["text"] and kind != "strike":
        problems.append(f"{path}.text: a {kind} needs text")
    if kind == "note":
        problems += [f"{path}.{name}: a note has none" for name in ("quote", "lines", "heading", "occurrence") if name in mark]
    else:
        problems += _anchor(mark, lines, path)
    return problems + _attachments(mark, number, effort, path)


def _readback_response(interaction: dict, body: dict, effort: Path) -> list[str]:
    problems = _answers(body, interaction["decisions"], interaction["number"], effort)
    verdict, marks = body.get("verdict"), body.get("marks")
    if verdict not in ("approve", "changes"):
        problems.append("verdict: must be approve or changes")
    if body.get("version") != interaction["version"] or not _integer(body.get("version")):
        problems.append(f"version: must be {interaction['version']}, the version shown")
    if not isinstance(marks, list):
        return problems + ["marks: required, a list"]
    if verdict == "approve" and marks:
        problems.append("marks: an approve carries none")
    kept = effort / "pilot" / "versions" / interaction["artifact"] / f"{interaction['version']:03d}.md"
    lines = len(kept.read_text().splitlines())
    for index, mark in enumerate(marks):
        problems += _mark(mark, index + 1, lines, interaction["number"], effort, f"marks[{index}]")
    return problems


def _pin(pin: object, keys: set[str], seen: dict[str, int], number: int, effort: Path, path: str) -> list[str]:
    """One comment of a verdict; `seen` counts each variant's comments so far, so `n` follows the order the pins were made."""
    if not isinstance(pin, dict):
        return [f"{path}: must be an object"]
    problems = _strings(pin, ("selector", "leading_text", "text"), f"{path}.")
    for name in ("selector", "text"):
        if pin.get(name) == "":
            problems.append(f"{path}.{name}: must not be empty")
    variant = pin.get("variant")
    if not isinstance(variant, str) or variant not in keys:
        return problems + [f"{path}.variant: must be one of {', '.join(sorted(keys))}"]
    seen[variant] = seen.get(variant, 0) + 1
    if pin.get("n") != seen[variant] or not _integer(pin["n"]):
        problems.append(f"{path}.n: must be {seen[variant]}, the next number for variant {variant}")
    return problems + _attachments(pin, number, effort, path)


def _prototype_response(interaction: dict, body: dict, effort: Path) -> list[str]:
    keys = {v["key"] for v in interaction["variants"]}
    problems = []
    if not isinstance(body.get("winner"), str) or body["winner"] not in keys:
        problems.append(f"winner: must be one of {', '.join(sorted(keys))}")
    for name in ("take", "leave_out"):
        if not isinstance(body.get(name), str) or not body[name]:
            problems.append(f"{name}: must be a non-empty string")
    problems += _attachments(body, interaction["number"], effort, "body")
    comments = body.get("comments")
    if not isinstance(comments, list):
        return problems + ["comments: required, a list"]
    seen: dict[str, int] = {}
    for index, pin in enumerate(comments):
        problems += _pin(pin, keys, seen, interaction["number"], effort, f"comments[{index}]")
    return problems


def response_problems(interaction: dict, body: object, effort: Path) -> list[str]:
    """Every way `body` fails the response contract for the stored `interaction`; empty when valid."""
    if not isinstance(body, dict):
        return ["body: must be a JSON object"]
    if interaction["kind"] == "prototype":
        return _prototype_response(interaction, body, effort)
    if interaction["kind"] == "readback":
        return _readback_response(interaction, body, effort)
    return _answers(body, interaction["questions"], interaction["number"], effort)
