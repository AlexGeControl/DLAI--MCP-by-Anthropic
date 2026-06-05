"""
DeepLearning.AI platform adapter — auth + fetch, folded into one module.

Strictly LOCAL and READ-ONLY: it decrypts the user's own Chrome cookies on this
machine to authenticate, reads course data, and never transmits credentials
anywhere except to deeplearning.ai itself (the same destination the browser uses).

Public surface:
    make_session()                         -> authenticated requests.Session
    trpc(session, proc, input)             -> parsed tRPC result (raises on error)
    get_user_id(session)                   -> int
    get_course(session, course_slug)       -> course dict (courseId, lessons, ...)
    fetch_subtitle(session, video_id)      -> list[{startInSeconds,endInSeconds,text}]
    boot_sandbox(session, prog_id, course_id, user_id, timeout=300) -> (host, token)
    crawl_sandbox(session, host, token, dest_dir) -> dict of counts

This is the DLAI-specific layer. Downstream skills (notes, staleness, refactor)
operate on the canonical on-disk layout produced by compile.py, NOT on this module,
so they stay platform-agnostic.
"""
import os, json, time, base64, hashlib, shutil, tempfile, sqlite3, urllib.parse

import requests
import secretstorage
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

CHROME_COOKIES = os.path.expanduser("~/.config/google-chrome/Default/Cookies")
TRPC_BASE = "https://learn.deeplearning.ai/api/trpc/"
SAFE_STORAGE_LABEL = "Chrome Safe Storage"   # NOT "Chrome Safe Storage Control"


# --------------------------------------------------------------------------- #
# Auth (folded in): decrypt local Chrome v11 cookies via gnome-keyring
# --------------------------------------------------------------------------- #
def _safe_storage_key(label=SAFE_STORAGE_LABEL):
    bus = secretstorage.dbus_init()
    col = secretstorage.get_default_collection(bus)
    for item in col.get_all_items():
        if item.get_label() == label:
            return item.get_secret()
    raise RuntimeError(f"Keyring item {label!r} not found (is Chrome's keyring unlocked?)")


def _derive_key(password):
    # Linux Chrome: PBKDF2-HMAC-SHA1, salt 'saltysalt', 1 iteration, 16-byte key
    return hashlib.pbkdf2_hmac("sha1", password, b"saltysalt", 1, 16)


def _decrypt(enc, key):
    if enc[:3] in (b"v10", b"v11"):
        enc = enc[3:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16), backend=default_backend())
    d = cipher.decryptor()
    out = d.update(enc) + d.finalize()
    out = out[: -out[-1]]  # strip PKCS7 padding
    try:
        return out.decode("utf-8")
    except UnicodeDecodeError:
        return out[32:].decode("utf-8", "replace")  # strip 32-byte domain-hash prefix


def _read_cookies(domain_like="deeplearning.ai"):
    key = _derive_key(_safe_storage_key())
    tmp = tempfile.mktemp()
    shutil.copy(CHROME_COOKIES, tmp)  # copy because Chrome holds a lock on the live DB
    try:
        con = sqlite3.connect(tmp)
        rows = con.execute(
            "select host_key, name, encrypted_value, path from cookies where host_key like ?",
            (f"%{domain_like}%",),
        ).fetchall()
        con.close()
    finally:
        os.unlink(tmp)
    out = []
    for host, name, enc, path in rows:
        try:
            val = _decrypt(enc, key) if enc else ""
        except Exception:
            val = ""
        if val:
            out.append((host, name, val, path))
    return out


def make_session(domain_like="deeplearning.ai"):
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html;q=0.9,*/*;q=0.8",
    })
    for host, name, val, path in _read_cookies(domain_like):
        s.cookies.set(name, val, domain=host.lstrip("."), path=path)
    return s


# --------------------------------------------------------------------------- #
# tRPC
# --------------------------------------------------------------------------- #
def trpc(session, proc, input_obj):
    q = urllib.parse.quote(json.dumps({"0": {"json": input_obj}}))
    r = session.get(f"{TRPC_BASE}{proc}?batch=1&input={q}", timeout=60,
                    headers={"Accept": "application/json"})
    payload = r.json()[0]
    if "error" in payload:
        err = payload["error"]["json"]
        raise RuntimeError(f"tRPC {proc} -> {err.get('message')}")
    return payload["result"]["data"]["json"]


def get_user_id(session):
    return int(trpc(session, "user.getUserProfile", {})["userId"])


def get_course(session, course_slug):
    return trpc(session, "course.getCourseBySlug", {"courseSlug": course_slug})


def fetch_subtitle(session, video_id):
    return trpc(session, "course.getLessonVideoSubtitle", {"videoId": video_id})["captions"]


# --------------------------------------------------------------------------- #
# Jupyter sandbox lifecycle (one sandbox holds ALL of a course's lab folders)
# --------------------------------------------------------------------------- #
def boot_sandbox(session, prog_assignment_id, course_id, user_id, timeout=300, interval=8):
    """getProgramLab boots a per-user sandbox; poll until it returns a notebook URL.
    Returns (host, token)."""
    inp = {"programAssignmentId": prog_assignment_id, "courseId": course_id, "userId": user_id}
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            info = trpc(session, "course.getProgramLab", inp)
            url = info["url"]
            host = url.split("/notebooks/")[0]
            token = url.split("token=")[1]
            return host, token
        except RuntimeError as e:
            last = str(e)
            time.sleep(interval)
    raise TimeoutError(f"sandbox not ready after {timeout}s (last: {last})")


def _contents(session, host, token, path=""):
    u = f"{host}/api/contents/{path}?token={token}&content=1"
    return session.get(u, timeout=60).json()


def crawl_sandbox(session, host, token, dest_dir):
    """Mirror the entire sandbox filesystem to dest_dir, verbatim. Notebooks are
    written as .ipynb JSON, binaries decoded from base64."""
    counts = {"file": 0, "notebook": 0, "dir": 0}

    def walk(path=""):
        node = _contents(session, host, token, path)
        if node["type"] == "directory":
            counts["dir"] += 1
            for item in node["content"]:
                walk(item["path"])
        else:
            dest = os.path.join(dest_dir, path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if node["type"] == "notebook":
                json.dump(node["content"], open(dest, "w"), indent=1)
                counts["notebook"] += 1
            elif node.get("format") == "base64":
                open(dest, "wb").write(base64.b64decode(node["content"]))
                counts["file"] += 1
            else:
                open(dest, "w").write(node["content"])
                counts["file"] += 1

    walk("")
    return counts


if __name__ == "__main__":
    # smoke test
    s = make_session()
    print("user_id:", get_user_id(s))
