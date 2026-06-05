#!/usr/bin/env python3
"""
Compile a DeepLearning.AI course into the canonical on-disk layout:

    <out>/
      manifest.json          # lessons + ids + crosswalk + provenance
      raw/transcripts/NN-slug.md
      raw/assignments/<sandbox tree, verbatim>

Downstream skills (notes / staleness / refactor) read ONLY this layout, never the
platform. To support a new platform later, write a sibling adapter + compile that
emits the same layout.

Usage:
    python compile.py <course-slug-or-url> [--out DIR] [--what transcripts,assignments]
    python compile.py <slug> --manifest-only         # rebuild manifest from course meta only
"""
import os, re, sys, json, argparse, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlai_adapter as dl


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_course_slug(arg):
    m = re.search(r"/courses/([^/]+)", arg)
    return m.group(1) if m else arg


def fmt_ts(sec):
    return f"{int(sec // 60):02d}:{int(sec % 60):02d}"


def write_transcript(lesson, captions, outdir):
    fn = f"{lesson['index']:02d}-{slugify(lesson['name'])}.md"
    with open(os.path.join(outdir, fn), "w") as f:
        f.write(f"# Lesson {lesson['index']}: {lesson['name']}\n\n")
        f.write(f"_slug: {lesson['slug']} · videoId: {lesson.get('videoId')} · "
                f"type: {lesson['type']} · ~{(lesson.get('time') or 0)/60:.1f} min_\n\n")
        if isinstance(captions, list):
            f.write(" ".join(c["text"] for c in captions).strip() + "\n\n")
            f.write("---\n\n## Timestamped\n\n")
            for c in captions:
                f.write(f"`[{fmt_ts(c['startInSeconds'])}]` {c['text']}\n")
        else:
            f.write(str(captions) + "\n")
    return fn


def build_manifest(course, lessons, out, transcript_files, assignment_counts, sandbox_url):
    return {
        "platform": "deeplearning.ai",
        "course_slug": course["slug"],
        "course_name": course["name"],
        "course_id": course["courseId"],
        "type": course.get("type"),
        "total_duration_seconds": course.get("totalDurationSeconds"),
        "compiled_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "sandbox_url_sample": sandbox_url,
        "assignment_file_counts": assignment_counts,
        "lessons": [
            {
                "index": l["index"],
                "slug": l["slug"],
                "name": l["name"],
                "type": l["type"],
                "video_id": l.get("videoId"),
                "program_id": l.get("programId"),   # -> programAssignmentId for getProgramLab
                "duration_seconds": l.get("time"),
                "transcript": transcript_files.get(l["slug"]),
            }
            for l in lessons
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("course", help="course slug or full lesson URL")
    ap.add_argument("--out", default=".", help="output root (default: cwd)")
    ap.add_argument("--what", default="transcripts,assignments,manifest")
    ap.add_argument("--manifest-only", action="store_true")
    args = ap.parse_args()

    what = set(args.what.split(",")) if not args.manifest_only else {"manifest"}
    slug = parse_course_slug(args.course)
    out = os.path.abspath(args.out)

    s = dl.make_session()
    user_id = dl.get_user_id(s)
    course = dl.get_course(s, slug)
    lessons = sorted(course["lessons"].values(), key=lambda l: l["index"])
    print(f"Course: {course['name']}  (id={course['courseId']}, user={user_id}, {len(lessons)} lessons)")

    transcript_files, counts, sandbox_url = {}, None, None

    if "transcripts" in what:
        tdir = os.path.join(out, "raw", "transcripts")
        os.makedirs(tdir, exist_ok=True)
        for l in lessons:
            vid = l.get("videoId")
            if not vid:
                print(f"  - skip transcript L{l['index']:02d} ({l['type']})")
                continue
            caps = dl.fetch_subtitle(s, vid)
            transcript_files[l["slug"]] = write_transcript(l, caps, tdir)
            print(f"  - transcript {transcript_files[l['slug']]}")

    if "assignments" in what:
        notebook_lessons = [l for l in lessons if l.get("programId")]
        if notebook_lessons:
            prog_id = notebook_lessons[0]["programId"]
            print(f"  booting sandbox via programId={prog_id} ...")
            host, token = dl.boot_sandbox(s, prog_id, course["courseId"], user_id)
            sandbox_url = host
            adir = os.path.join(out, "raw", "assignments")
            os.makedirs(adir, exist_ok=True)
            counts = dl.crawl_sandbox(s, host, token, adir)
            print(f"  assignments mirrored: {counts}")
        else:
            print("  no notebook lessons with a programId; skipping assignments")

    if "manifest" in what:
        # if transcripts weren't re-fetched this run, recover filenames from disk
        if not transcript_files:
            tdir = os.path.join(out, "raw", "transcripts")
            if os.path.isdir(tdir):
                by_idx = {f"{l['index']:02d}": l for l in lessons}
                for fn in os.listdir(tdir):
                    key = fn[:2]
                    if key in by_idx:
                        transcript_files[by_idx[key]["slug"]] = fn
        manifest = build_manifest(course, lessons, out, transcript_files, counts, sandbox_url)
        with open(os.path.join(out, "manifest.json"), "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"  manifest.json written ({len(lessons)} lessons)")


if __name__ == "__main__":
    main()
