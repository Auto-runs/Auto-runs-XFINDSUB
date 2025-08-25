import argparse
import asyncio
import json
import sys
from pathlib import Path

from sources import crtsh, otx, bufferover
from resolver import resolve  # async bool(sub)

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
import pyfiglet

# Console untuk LOG ke stderr (biar hasil subdomain ke stdout tetap bersih)
log = Console(stderr=True, highlight=False, soft_wrap=False)

BANNER_COLOR = "bold cyan"
ACCENT = "bright_magenta"
OK = "bold green"
WARN = "yellow"
ERR = "bold red"

DEFAULT_SOURCES = ["crtsh", "otx", "bufferover"]


def print_banner():
    art = pyfiglet.figlet_format("XFINDSUB")
    log.print(f"[{BANNER_COLOR}]{art}[/{BANNER_COLOR}]")
    log.print(f"[{ACCENT}]Passive Subdomain Finder • xfindsub[/]  |  Made with Auto-runs \n")


async def run_sources(domain: str, enabled: list[str]) -> set[str]:
    subs: set[str] = set()
    results: list[set[str]] = []

    with Progress(
        SpinnerColumn(style=ACCENT),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=log,
        transient=True,
    ) as prog:
        tasks = []
        task_map = {}

        if "crtsh" in enabled:
            t = prog.add_task("[*] crtsh", total=None)
            task_map["crtsh"] = t
            tasks.append(("crtsh", crtsh.fetch(domain)))
        if "otx" in enabled:
            t = prog.add_task("[*] otx", total=None)
            task_map["otx"] = t
            tasks.append(("otx", otx.fetch(domain)))
        if "bufferover" in enabled:
            t = prog.add_task("[*] bufferover", total=None)
            task_map["bufferover"] = t
            tasks.append(("bufferover", bufferover.fetch(domain)))

        coros = [c for _, c in tasks]
        results = await asyncio.gather(*coros, return_exceptions=True)

        for (name, _), res in zip(tasks, results):
            if isinstance(res, Exception):
                prog.update(task_map[name], description=f"[x] {name} error")
                continue
            subs.update(res)
            prog.update(task_map[name], description=f"[✔] {name}: {len(res)} found")

    # Normalisasi hasil
    cleaned = {s.lower().strip().rstrip(".") for s in subs if s and "." in s}
    return cleaned



async def resolve_all(subs: list[str], concurrency: int = 100) -> list[str]:
    sem = asyncio.Semaphore(concurrency)
    out = []

    async def worker(host: str):
        async with sem:
            try:
                ok = await resolve(host)
                if ok:
                    out.append(host)
            except Exception:
                pass

    await asyncio.gather(*(worker(s) for s in subs))
    return out


async def process_domain(domain: str, sources: list[str], do_resolve: bool, show_progress: bool):
    subs = set()

    # spinner fetch
    if show_progress:
        with Progress(
            SpinnerColumn(style=ACCENT),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=log,
            transient=True,
        ) as prog:
            t1 = prog.add_task(f"[*] Fetching subdomains from sources …", total=None)
            subs = await run_sources(domain, sources)
            prog.update(t1, description=f"[✔] Collected candidates: {len(subs)}")
            prog.stop()
    else:
        subs = await run_sources(domain, sources)

    if do_resolve and subs:
        if show_progress:
            with Progress(
                SpinnerColumn(style=ACCENT),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=log,
                transient=True,
            ) as prog:
                t2 = prog.add_task("[*] Resolving DNS records …", total=None)
                resolved = await resolve_all(sorted(subs))
                prog.update(t2, description=f"[✔] Active subdomains: {len(resolved)}")
                prog.stop()
        else:
            resolved = await resolve_all(sorted(subs))
        return sorted(set(resolved))

    return sorted(subs)


def load_domains(single: str | None, list_path: str | None) -> list[str]:
    domains: list[str] = []
    if single:
        domains.append(single.strip())
    if list_path:
        p = Path(list_path)
        if not p.exists():
            log.print(f"[{ERR}]! list file not found:[/] {list_path}")
            sys.exit(2)
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line:
                domains.append(line)
    if not domains:
        log.print(f"[{ERR}]! provide -d or -l[/]")
        sys.exit(2)
    # sanitize
    norm = []
    for d in domains:
        d = d.lower().strip()
        for prefix in ("http://", "https://", "www."):
            if d.startswith(prefix):
                d = d[len(prefix):]
        norm.append(d)
    return sorted(set(norm))


def parse_args():
    ap = argparse.ArgumentParser(
        prog="xfindsub",
        description="xfindsub - passive subdomain enumeration (clean output, metasploit-like UI)",
    )
    ap.add_argument("-d", "--domain", help="single target domain")
    ap.add_argument("-l", "--list", help="path to file with domains (one per line)")
    ap.add_argument("--resolve", action="store_true", help="validate by DNS resolve (A/AAAA)")
    ap.add_argument("-o", "--output", help="write subdomains (one per line) to TXT")
    ap.add_argument("--json", help="write full results to JSON")
    ap.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                    help=f"comma-separated sources (default: {','.join(DEFAULT_SOURCES)})")
    ap.add_argument("--silent", action="store_true",
                    help="only print subdomains to stdout (no banner/logs)")
    return ap.parse_args()


def write_txt(path: str, items: list[str]):
    Path(path).write_text("\n".join(items) + ("\n" if items else ""), encoding="utf-8")
    log.print(f"[{OK}][+] saved TXT[/]: {path} ({len(items)})")


def write_json(path: str, data: dict):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    log.print(f"[{OK}][+] saved JSON[/]: {path}")


def main():
    args = parse_args()
    domains = load_domains(args.domain, args.list)
    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]

    if not args.silent:
        print_banner()
        log.print(f"[{OK}][+] Target  :[/] {', '.join(domains)}")
        log.print(f"[{OK}][+] Sources :[/] {', '.join(sources)}")
        log.print(f"[{OK}][+] Resolve :[/] {'ON' if args.resolve else 'OFF'}\n")

    results_map: dict[str, list[str]] = {}
    total = 0

    for d in domains:
        if not args.silent:
            log.print(f"[{ACCENT}]--- {d} ---[/]")
        subs = asyncio.run(process_domain(d, sources, args.resolve, show_progress=not args.silent))
        results_map[d] = subs
        total += len(subs)

        # OUTPUT BERSIH ke stdout: 1 subdomain per baris
        for s in subs:
            print(s)

        if not args.silent:
            log.print(f"[{OK}][✔] {d}: {len(subs)} subdomains[/]\n")

    if args.output:
        # Flatten unik untuk TXT
        flat = sorted({s for arr in results_map.values() for s in arr})
        write_txt(args.output, flat)

    if args.json:
        write_json(args.json, results_map)

    if not args.silent:
        log.print(f"\n[{OK}]Done! Total subdomains: {total}[/]")


if __name__ == "__main__":
    main()
