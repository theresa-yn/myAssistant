from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import langid

from .config import get_db_path


@dataclass
class Memory:
	id: int
	text: str
	language: str
	tags: str
	source: str
	created_at: str


class MemoryStore:
	def __init__(self, db_path: Optional[Path] = None) -> None:
		self.db_path = str(db_path or get_db_path())
		self._ensure_schema()

	@contextmanager
	def _conn(self):
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		try:
			yield conn
			conn.commit()
		finally:
			conn.close()

	def _ensure_schema(self) -> None:
		with self._conn() as conn:
			conn.execute("PRAGMA foreign_keys=ON;")
			conn.execute(
				"""
				CREATE TABLE IF NOT EXISTS memories (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					text TEXT NOT NULL,
					language TEXT NOT NULL,
					tags TEXT NOT NULL DEFAULT '',
					source TEXT NOT NULL DEFAULT '',
					created_at TEXT NOT NULL
				);
				"""
			)
			# FTS5 virtual table for full-text search; contentless with external content
			conn.execute(
				"""
				CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
					text, tags, source, language, content='memories', content_rowid='id'
				);
				"""
			)
			# Triggers to keep FTS in sync
			conn.executescript(
				"""
				CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
					INSERT INTO memories_fts(rowid, text, tags, source, language)
					VALUES (new.id, new.text, new.tags, new.source, new.language);
				END;
				CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
					INSERT INTO memories_fts(memories_fts, rowid, text, tags, source, language)
					VALUES('delete', old.id, old.text, old.tags, old.source, old.language);
				END;
				CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
					INSERT INTO memories_fts(memories_fts, rowid, text, tags, source, language)
					VALUES('delete', old.id, old.text, old.tags, old.source, old.language);
					INSERT INTO memories_fts(rowid, text, tags, source, language)
					VALUES (new.id, new.text, new.tags, new.source, new.language);
				END;
				"""
			)

	def remember(self, text: str, tags: Optional[Sequence[str]] = None, source: str = "") -> int:
		if not text.strip():
			raise ValueError("Memory text cannot be empty")
		language, _ = langid.classify(text)
		tags_str = " ".join(tags or [])
		created_at = datetime.now(timezone.utc).isoformat()
		with self._conn() as conn:
			cur = conn.execute(
				"INSERT INTO memories(text, language, tags, source, created_at) VALUES (?, ?, ?, ?, ?)",
				(text, language, tags_str, source or "", created_at),
			)
			return int(cur.lastrowid)

	def list_recent(self, limit: int = 20) -> List[Memory]:
		with self._conn() as conn:
			rows = conn.execute(
				"SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,)
			).fetchall()
			return [self._row_to_memory(r) for r in rows]

	def ask(self, query: str, limit: int = 5) -> List[Tuple[Memory, float]]:
		# Use FTS5 BM25 ranking
		if not query.strip():
			return []
		with self._conn() as conn:
			rows = conn.execute(
				"""
				SELECT m.*, bm25(memories_fts) AS score
				FROM memories_fts JOIN memories m ON m.id = memories_fts.rowid
				WHERE memories_fts MATCH ?
				ORDER BY score LIMIT ?
				""",
				(query, limit),
			).fetchall()
			return [(self._row_to_memory(r), float(r["score"])) for r in rows]

	def delete(self, memory_id: int) -> None:
		with self._conn() as conn:
			conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

	@staticmethod
	def _row_to_memory(row: sqlite3.Row) -> Memory:
		return Memory(
			id=int(row["id"]),
			text=str(row["text"]),
			language=str(row["language"]),
			tags=str(row["tags"]),
			source=str(row["source"]),
			created_at=str(row["created_at"]),
		)

