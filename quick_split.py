"""The Forge 649 · the Windows app's quicker start: the full page, split into the page the app opens and the apps it carries,
each in a script beside it (blocks/forge_quick_file.html runs one the first time it is wanted).

  python quick_split.py split THE_FORGE.html OUT_DIR
      writes OUT_DIR/the_forge.html (the quick page) and OUT_DIR/the_forge_parts/<id>.js for each carried app, and checks
      that putting each part back in its place gives the full page again, byte for byte;
  python quick_split.py join QUICK.html PARTS_DIR THE_FORGE.html
      puts the parts back and ends with an error unless that gives THE_FORGE.html exactly.

The Windows app opens its page from the disk, at the address where her work is kept; a page opened that way may run a script
beside it but may not read the file as text, so each part is a script that hands its text to the page. The Mac app serves its
folder and takes text parts (forge_644/forge_quick_split.py). Any other copy is the full page and needs no parts. Copied into
the Forge-windows repository as quick_split.py by forge_repo_649.py."""
import hashlib, os, re, sys

IDS = ("forge-bi-ingenium", "forge-bi-cd", "forge-bi-self", "forge-bi-inkwell")
HEAD, MID, TAIL = b'window.__forgePart&&window.__forgePart("', b'","', b'");\n'


def split(full):
    if b'id="forge-bi-meta"' not in full:
        sys.exit("give the full page (it carries its apps)")
    if b'id="forge-649-quick-file"' not in full:
        sys.exit("this page cannot read its parts from scripts (blocks/forge_quick_file.html): build it with forge649.py first")
    page, parts = full, {}
    for ident in IDS:
        m = re.search(rb'(<script\b[^>]*\bid="' + ident.encode() + rb'"[^>]*)>([^<]*)</script>', page)
        if not m:
            sys.exit("the page does not carry " + ident)
        if not re.fullmatch(rb"[A-Za-z0-9+/=]+", m.group(2)):
            sys.exit(ident + ": not plain base64, so it cannot go into a script as it is")
        parts[ident] = m.group(2)
        tag = m.group(1) + b' data-defer="the_forge_parts/' + ident.encode() + b'.js">'
        page = page[:m.start()] + tag + b"</script>" + page[m.end():]
    return page, parts


def join(page, parts):
    for ident, body in parts.items():
        place = b' data-defer="the_forge_parts/' + ident.encode() + b'.js"></script>'
        if page.count(place) != 1:
            sys.exit("the quick page has no single place for " + ident)
        page = page.replace(place, b">" + body + b"</script>", 1)
    return page


def read_part(path, ident):
    t = open(path, "rb").read()
    want = HEAD + ident.encode() + MID
    if not (t.startswith(want) and t.endswith(TAIL)):
        sys.exit(path + ": not a part of the Forge's page")
    body = t[len(want):-len(TAIL)]
    if not re.fullmatch(rb"[A-Za-z0-9+/=]+", body):
        sys.exit(path + ": its text is not plain base64")
    return body


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "split":
        full = open(sys.argv[2], "rb").read()
        out = sys.argv[3]
        page, parts = split(full)
        if join(page, parts) != full:
            sys.exit("the parts put back do not give the full page again")
        os.makedirs(os.path.join(out, "the_forge_parts"), exist_ok=True)
        open(os.path.join(out, "the_forge.html"), "wb").write(page)
        for ident, body in parts.items():
            open(os.path.join(out, "the_forge_parts", ident + ".js"), "wb").write(HEAD + ident.encode() + MID + body + TAIL)
        print("quick page %.1f MB (full %.1f MB), %d parts: %s; full page sha256 %s" % (len(page) / 1e6, len(full) / 1e6, len(parts),
              ", ".join("%s %.1f MB" % (k, len(v) / 1e6) for k, v in parts.items()), hashlib.sha256(full).hexdigest()[:16]))
    elif len(sys.argv) == 5 and sys.argv[1] == "join":
        page = open(sys.argv[2], "rb").read()
        parts = {ident: read_part(os.path.join(sys.argv[3], ident + ".js"), ident) for ident in IDS}
        full = open(sys.argv[4], "rb").read()
        back = join(page, parts)
        print("put back: %s; the full page: %s" % (hashlib.sha256(back).hexdigest(), hashlib.sha256(full).hexdigest()))
        if back != full:
            sys.exit("the quick page and its parts do not give the full page")
    else:
        sys.exit(__doc__)
