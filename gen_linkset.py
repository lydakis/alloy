import json

import mkdocs_gen_files


def to_dir_url(site: str, path: str) -> str:
    # path is something like 'index.md', 'foo.md', 'foo/index.md', 'docs/bar.md'
    if path.endswith(".markdown"):
        stem = path[: -len(".markdown")]
    else:
        stem = path[: -len(".md")]

    stem = stem.rstrip("/")
    if stem.endswith("/index") or stem == "index":
        stem = stem[: -len("/index")] if stem.endswith("/index") else ""
    url_path = f"{stem}/" if stem else ""
    return f"{site}/{url_path}"


def main() -> None:
    cfg = mkdocs_gen_files.config
    site = cfg["site_url"].rstrip("/")

    links = []
    for page in mkdocs_gen_files.files:
        if not (page.endswith(".md") or page.endswith(".markdown")):
            continue
        url = to_dir_url(site, page)
        links.append({"rel": "item", "href": url})

    data = {"linkset": [{"anchor": f"{site}/", "link": links}]}
    for name in [".well-known/linkset", ".well-known/linkset.json"]:
        with mkdocs_gen_files.open(name, "w") as f:
            f.write(json.dumps(data))


if __name__ == "__main__":
    main()
