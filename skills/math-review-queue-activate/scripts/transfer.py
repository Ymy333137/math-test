#!/usr/bin/env python3
"""Preview and activate indexed math questions; Python 3.9+ standard library only."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path


HISTORY_FIELDS = (
    "question_id", "display_id", "display_label", "page", "section",
    "question_type", "record_order", "target_score_tier",
    "required_for_scores", "error_level", "mastery", "performance_level",
)
MATCH_FIELDS = ("question_id", "display_id", "display_label", "page", "record_order", "error_level")
DECODER = json.JSONDecoder()


def fail(message):
    raise ValueError(message)


def load_file(path):
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
        source = raw.decode("utf-8")
    except (UnicodeError, json.JSONDecodeError) as exc:
        fail("Invalid UTF-8 JSON in {}: {}".format(path, exc))
    if not isinstance(value, dict):
        fail("Expected a JSON object: {}".format(path))
    return raw, source, value


def nested_values(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from nested_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_values(child)
    elif isinstance(value, str):
        yield value


def require_list(obj, field):
    value = obj.get(field)
    if not isinstance(value, list):
        fail("Expected array at {}".format(field))
    return value


def require_dict(obj, field):
    value = obj.get(field)
    if not isinstance(value, dict):
        fail("Expected object at {}".format(field))
    return value


def plan_data(pending, canonical, schedule, count, day, unit):
    items = require_list(pending, "items")
    records = require_list(canonical, "records")
    history = require_list(canonical, "history")
    buckets = require_dict(schedule, "buckets")
    daily = require_dict(schedule, "daily_plans")
    for name, mapping in (("buckets", buckets), ("daily_plans", daily)):
        for key, value in mapping.items():
            if not isinstance(value, list):
                fail("Expected array at {}[{}]".format(name, key))
    if len(items) < count:
        fail("Only {} pending items remain; requested {}".format(len(items), count))
    ids = [item.get("question_id") if isinstance(item, dict) else None for item in items]
    if any(not isinstance(qid, str) or not qid for qid in ids) or len(set(ids)) != len(ids):
        fail("Pending question IDs are missing or duplicated")
    record_counts = Counter(r.get("question_id") for r in records if isinstance(r, dict))
    history_counts = Counter(h.get("question_id") for h in history if isinstance(h, dict))
    selected = items[:count]
    full_records = []
    keys = []
    for item in selected:
        qid = item["question_id"]
        if record_counts[qid] > 1:
            fail("Duplicate canonical record: {}".format(qid))
        record = next((r for r in records if isinstance(r, dict) and r.get("question_id") == qid), None)
        if history_counts[qid]:
            fail("Already active in history: {}".format(qid))
        for field in MATCH_FIELDS:
            if field not in item:
                fail("Pending item {} lacks {}".format(qid, field))
            if record is not None and (field not in record or item[field] != record[field]):
                fail("Pending/canonical mismatch at {}: {}".format(qid, field))
        if item["error_level"] not in ("A", "B", "C"):
            fail("Unrecognized grade for {}".format(qid))
        if record is not None:
            for field in HISTORY_FIELDS:
                if field not in record:
                    fail("Canonical record {} lacks {}".format(qid, field))
            if record.get("unit") != unit:
                fail("Canonical record {} belongs to another workbook".format(qid))
            if not isinstance(record.get("curriculum_unit"), str):
                fail("Canonical record {} has no curriculum unit".format(qid))
        else:
            if not isinstance(item["page"], int) or item["page"] < 1:
                fail("Invalid page for {}".format(qid))
            if not isinstance(item["record_order"], int) or item["record_order"] < 1:
                fail("Invalid record order for {}".format(qid))
            parts = item["display_label"].split(" · ")
            if len(parts) != 3 or parts[2] != item["display_id"] or parts[1] not in ("选择题", "填空题", "解答题"):
                fail("Cannot derive section/type safely from {}".format(qid))
        key = unit + ":" + qid
        for container in ("buckets", "daily_plans", "release_buffer", "backlog", "forced_releases"):
            if key in nested_values(schedule.get(container, {})):
                fail("Already scheduled in {}: {}".format(container, key))
        full_records.append(record)
        keys.append(key)
    for name, mapping in (("buckets", buckets), ("daily_plans", daily)):
        target = mapping.get(day, [])
        if not isinstance(target, list) or len(target) != len(set(target)):
            fail("Target {}[{}] is invalid or duplicated".format(name, day))
    return selected, full_records, keys


def index_record(item, args):
    section, question_type, _ = item["display_label"].split(" · ")
    profile = {
        "A": (0.65, 0.60, 0.49, "不佳"),
        "B": (0.70, 0.50, 0.62, "合格"),
        "C": (0.20, 0.40, 0.28, "不佳"),
    }
    correctness, thinking_quality, mastery, performance = profile[item["error_level"]]
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unit": args.unit,
        "curriculum_unit": args.curriculum_unit,
        **item,
        "section": section,
        "question_type": question_type,
        "target_score_tier": args.target_score_tier,
        "required_for_scores": args.required_scores.split(","),
        "source_label": "题册" + args.unit.removeprefix("workbook_"),
        "assessment_basis": "pending_index",
        "question_md": "### " + item["display_id"],
        "correctness": correctness,
        "thinking_quality": thinking_quality,
        "mastery": mastery,
        "performance_level": performance,
    }


def fingerprint(raws, args):
    digest = hashlib.sha256()
    for part in (args.pending, args.record, args.schedule, args.unit, args.curriculum_unit,
                 args.target_score_tier, args.required_scores, args.date, str(args.count)):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    for raw in raws:
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def ws(source, pos):
    while pos < len(source) and source[pos].isspace():
        pos += 1
    return pos


def member_span(source, key, object_start=0):
    pos = ws(source, object_start)
    if source[pos] != "{":
        fail("Unexpected JSON object layout")
    pos = ws(source, pos + 1)
    while source[pos] != "}":
        name, end_name = DECODER.raw_decode(source, pos)
        if not isinstance(name, str):
            fail("Unexpected JSON member")
        start_value = ws(source, end_name)
        if source[start_value] != ":":
            fail("Unexpected JSON separator")
        start_value = ws(source, start_value + 1)
        _, end_value = DECODER.raw_decode(source, start_value)
        if name == key:
            return start_value, end_value
        pos = ws(source, end_value)
        if source[pos] == ",":
            pos = ws(source, pos + 1)
        elif source[pos] != "}":
            fail("Unexpected JSON object ending")
    return None


def elements(source, start, end):
    if source[start] != "[" or source[end - 1] != "]":
        fail("Unexpected JSON array layout")
    pos = ws(source, start + 1)
    found = []
    while pos < end - 1 and source[pos] != "]":
        _, finish = DECODER.raw_decode(source, pos)
        found.append((pos, finish))
        pos = ws(source, finish)
        if source[pos] == ",":
            pos = ws(source, pos + 1)
        elif source[pos] != "]":
            fail("Unexpected JSON array ending")
    return found


def pretty(value, indent):
    return "\n".join(" " * indent + line for line in json.dumps(value, ensure_ascii=False, indent=2).splitlines())


def edit_array(source, span, *, remove=0, prepend=None, append=None, indent=4):
    start, end = span
    spans = elements(source, start, end)
    if remove:
        if remove > len(spans):
            fail("Array shorter than planned removal")
        if remove == len(spans):
            body = ""
        else:
            body = "\n" + " " * indent + source[spans[remove][0]:end - 1]
        return source[:start + 1] + body + source[end - 1:]
    new = prepend if prepend is not None else append
    if not new:
        return source
    rendered = ",\n".join(pretty(obj, indent) for obj in new)
    if prepend is not None:
        if spans:
            insertion = rendered + ",\n" + " " * indent
            at = spans[0][0]
            return source[:at] + insertion + source[at:]
    else:
        if spans:
            at = spans[-1][1]
            return source[:at] + ",\n" + rendered + source[at:]
    return source[:start + 1] + "\n" + rendered + "\n" + " " * (indent - 2) + source[end - 1:]


def edit_dated_array(source, parent, day, keys):
    parent_span = member_span(source, parent)
    if parent_span is None:
        fail("Missing {} object".format(parent))
    start, end = parent_span
    target_span = member_span(source, day, start)
    if target_span:
        return edit_array(source, target_span, prepend=keys, indent=6)
    rendered = "[\n" + ",\n".join(pretty(key, 6) for key in keys) + "\n    ]"
    existing = source[start + 1:end - 1].strip()
    if existing:
        # Insert before the first existing key without changing other dates.
        first = ws(source, start + 1)
        return source[:first] + json.dumps(day) + ": " + rendered + ",\n    " + source[first:]
    return source[:start + 1] + "\n    " + json.dumps(day) + ": " + rendered + "\n  " + source[end - 1:]


def make_outputs(sources, pending, canonical, schedule, selected, records, keys, day):
    pending_text, record_text, schedule_text = sources
    pending_text = edit_array(pending_text, member_span(pending_text, "items"), remove=len(selected))
    original_ids = {record.get("question_id") for record in canonical["records"]}
    created = [record for record in records if record["question_id"] not in original_ids]
    if created:
        record_text = edit_array(record_text, member_span(record_text, "records"), append=created)
    history_entries = []
    for record in records:
        entry = {field: record[field] for field in HISTORY_FIELDS if field != "unit"}
        entry["unit"] = record["curriculum_unit"]
        history_entries.append(entry)
    record_text = edit_array(record_text, member_span(record_text, "history"), append=history_entries)
    schedule_text = edit_dated_array(schedule_text, "buckets", day, keys)
    schedule_text = edit_dated_array(schedule_text, "daily_plans", day, keys)
    updated_span = member_span(schedule_text, "updated_at")
    if updated_span:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        schedule_text = schedule_text[:updated_span[0]] + json.dumps(now) + schedule_text[updated_span[1]:]
    out_pending, out_record, out_schedule = map(json.loads, (pending_text, record_text, schedule_text))
    selected_ids = {item["question_id"] for item in selected}
    if len(out_pending["items"]) != len(pending["items"]) - len(selected):
        fail("Pending count changed unexpectedly")
    if out_pending["items"] != pending["items"][len(selected):]:
        fail("Remaining pending order changed unexpectedly")
    if any(item["question_id"] in selected_ids for item in out_pending["items"]):
        fail("Selected item remains pending")
    if len(out_record["history"]) != len(canonical["history"]) + len(selected):
        fail("History count changed unexpectedly")
    if out_record["history"][:len(canonical["history"])] != canonical["history"]:
        fail("Existing history changed unexpectedly")
    if len(out_record["records"]) != len(canonical["records"]) + len(created):
        fail("Canonical records changed unexpectedly")
    if out_record["records"][:len(canonical["records"])] != canonical["records"]:
        fail("Existing canonical records changed unexpectedly")
    for qid in selected_ids:
        if sum(record.get("question_id") == qid for record in out_record["records"]) != 1:
            fail("Selected ID lacks exactly one canonical record: {}".format(qid))
        if sum(entry.get("question_id") == qid for entry in out_record["history"]) != 1:
            fail("Selected ID lacks exactly one history entry: {}".format(qid))
    for field in ("buckets", "daily_plans"):
        before = schedule[field].get(day, [])
        after = out_schedule[field][day]
        if after != keys + before or len(after) != len(set(after)):
            fail("{} order/count invalid".format(field))
    return (pending_text, record_text, schedule_text), out_schedule


def perform(args):
    root = Path(args.root).resolve(strict=True)
    if not root.is_dir():
        fail("Project root is not a directory")
    names = (args.pending, args.record, args.schedule)
    if len(set(names)) != 3 or any(Path(name).name != name for name in names):
        fail("File names must be three distinct base names")
    paths = tuple(root / name for name in names)
    if any(path.is_symlink() or not path.is_file() for path in paths):
        fail("Each data file must be a regular file in the project root")
    lock = root / ".math-review-queue-activate.lock"
    lock_fd = None
    if args.action == "apply":
        try:
            lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(lock_fd, str(os.getpid()).encode("ascii"))
        except FileExistsError:
            fail("Transfer lock exists; inspect it before retrying: {}".format(lock))
    staged = []
    recovery = None
    try:
        loaded = tuple(load_file(path) for path in paths)
        raws, sources, values = zip(*loaded)
        pending, canonical, schedule = values
        selected, existing_records, keys = plan_data(pending, canonical, schedule, args.count, args.date, args.unit)
        records = [record if record is not None else index_record(item, args)
                   for item, record in zip(selected, existing_records)]
        token = fingerprint(raws, args)
        report = {
            "date": args.date, "count": args.count, "ids": [item["question_id"] for item in selected],
            "pending_before": len(pending["items"]), "pending_after": len(pending["items"]) - args.count,
            "target_before": len(schedule["buckets"].get(args.date, [])),
            "target_after": len(schedule["buckets"].get(args.date, [])) + args.count,
            "metadata_records_to_create": sum(record is None for record in existing_records),
            "token": token,
        }
        if args.action == "plan":
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return
        if args.token != token:
            fail("Stale or mismatched plan token; no files changed")
        outputs, _ = make_outputs(sources, pending, canonical, schedule, selected, records, keys, args.date)
        for path, output in zip(paths, outputs):
            fd, temp_name = tempfile.mkstemp(prefix="." + path.name + ".stage-", dir=root)
            stage = Path(temp_name)
            staged.append(stage)
            os.fchmod(fd, stat.S_IMODE(path.stat().st_mode))
            with os.fdopen(fd, "wb") as stream:
                stream.write(output.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
        if any(path.read_bytes() != raw for path, raw in zip(paths, raws)):
            fail("A source file changed before replacement; no files changed by this run")
        recovery = Path(tempfile.mkdtemp(prefix="math-review-queue-activate-recovery-"))
        for path, raw in zip(paths, raws):
            (recovery / path.name).write_bytes(raw)
        replaced = []
        try:
            for path, raw, stage in zip(paths, raws, staged):
                if path.read_bytes() != raw:
                    fail("A source file changed during replacement")
                os.replace(stage, path)
                replaced.append(path)
        except Exception:
            # Restore only if our own new bytes are still present; never clobber a concurrent edit.
            for path, original, output in zip(paths, raws, outputs):
                if path in replaced and path.read_bytes() == output.encode("utf-8"):
                    path.write_bytes(original)
            raise
        shutil.rmtree(recovery)
        recovery = None
        report["status"] = "applied"
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception as exc:
        if recovery:
            print("Recovery copies retained at {}".format(recovery), file=sys.stderr)
        raise
    finally:
        for stage in staged:
            if stage.exists():
                stage.unlink()
        if lock_fd is not None:
            os.close(lock_fd)
            lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "apply"))
    parser.add_argument("--root", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--count", required=True, type=int)
    parser.add_argument("--pending", default="workbook_880_unscheduled.json")
    parser.add_argument("--record", default="880-record.json")
    parser.add_argument("--schedule", default="review_schedule.json")
    parser.add_argument("--unit", default="workbook_880")
    parser.add_argument("--curriculum-unit", default="unit_unassigned")
    parser.add_argument("--target-score-tier", default="120以下")
    parser.add_argument("--required-scores", default="120以下,120+")
    parser.add_argument("--token")
    args = parser.parse_args()
    try:
        if args.count < 1:
            fail("Count must be positive")
        if date.fromisoformat(args.date).isoformat() != args.date:
            fail("Date must be YYYY-MM-DD")
        if args.action == "apply" and not args.token:
            fail("Apply requires the token from plan")
        if not args.unit or not args.curriculum_unit or not args.target_score_tier or not all(args.required_scores.split(",")):
            fail("Metadata defaults must be nonempty")
        perform(args)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
