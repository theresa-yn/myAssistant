from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .memory_store import MemoryStore


def cmd_remember(args: argparse.Namespace) -> int:
	store = MemoryStore()
	memory_id = store.remember(args.text, args.tags or [], args.source or "")
	print(json.dumps({"id": memory_id}, ensure_ascii=False))
	return 0


def cmd_ask(args: argparse.Namespace) -> int:
	store = MemoryStore()
	pairs = store.ask(args.query, limit=args.limit)
	out = [
		{
			"id": m.id,
			"text": m.text,
			"language": m.language,
			"tags": [t for t in m.tags.split(" ") if t],
			"source": m.source,
			"created_at": m.created_at,
			"score": score,
		}
		for m, score in pairs
	]
	print(json.dumps(out, ensure_ascii=False, indent=2))
	return 0


def cmd_list(args: argparse.Namespace) -> int:
	store = MemoryStore()
	mems = store.list_recent(limit=args.limit)
	out = [
		{
			"id": m.id,
			"text": m.text,
			"language": m.language,
			"tags": [t for t in m.tags.split(" ") if t],
			"source": m.source,
			"created_at": m.created_at,
		}
		for m in mems
	]
	print(json.dumps(out, ensure_ascii=False, indent=2))
	return 0


def build_parser() -> argparse.ArgumentParser:
	p = argparse.ArgumentParser(prog="assistant", description="Personal memory assistant CLI")
	sub = p.add_subparsers(dest="cmd", required=True)

	p_rem = sub.add_parser("remember", help="Remember a piece of text")
	p_rem.add_argument("text", help="Text to remember")
	p_rem.add_argument("--tags", nargs="*", help="Optional tags")
	p_rem.add_argument("--source", default="", help="Optional source")
	p_rem.set_defaults(func=cmd_remember)

	p_ask = sub.add_parser("ask", help="Query memories")
	p_ask.add_argument("query", help="Search query")
	p_ask.add_argument("--limit", type=int, default=5, help="Max results")
	p_ask.set_defaults(func=cmd_ask)

	p_list = sub.add_parser("list", help="List recent memories")
	p_list.add_argument("--limit", type=int, default=20, help="Max items")
	p_list.set_defaults(func=cmd_list)
	return p


def main(argv: List[str] | None = None) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)
	return args.func(args)


if __name__ == "__main__":
	sys.exit(main())

