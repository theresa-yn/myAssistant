from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .memory_store import MemoryStore, Memory

app = FastAPI(title="MyAssistant API", version="0.1.0")
store = MemoryStore()


class RememberRequest(BaseModel):
	text: str = Field(..., min_length=1)
	tags: Optional[List[str]] = None
	source: Optional[str] = ""


class MemoryResponse(BaseModel):
	id: int
	text: str
	language: str
	tags: List[str]
	source: str
	created_at: str

	@classmethod
	def from_memory(cls, m: Memory) -> "MemoryResponse":
		return cls(
			id=m.id,
			text=m.text,
			language=m.language,
			tags=[t for t in m.tags.split(" ") if t],
			source=m.source,
			created_at=m.created_at,
		)


class AskResponseItem(BaseModel):
	memory: MemoryResponse
	score: float


class AskResponse(BaseModel):
	results: List[AskResponseItem]


@app.post("/remember", response_model=MemoryResponse)
def remember(req: RememberRequest) -> MemoryResponse:
	memory_id = store.remember(req.text, req.tags or [], req.source or "")
	for m in store.list_recent(limit=1):
		if m.id == memory_id:
			return MemoryResponse.from_memory(m)
	raise HTTPException(status_code=500, detail="Failed to fetch created memory")


@app.get("/recent", response_model=List[MemoryResponse])
def recent(limit: int = 20) -> List[MemoryResponse]:
	return [MemoryResponse.from_memory(m) for m in store.list_recent(limit=limit)]


@app.get("/ask", response_model=AskResponse)
def ask(q: str, limit: int = 5) -> AskResponse:
	pairs = store.ask(q, limit=limit)
	return AskResponse(
		results=[
			AskResponseItem(memory=MemoryResponse.from_memory(m), score=score)
			for m, score in pairs
		]
	)


@app.delete("/memories/{memory_id}")
def delete(memory_id: int) -> dict:
	store.delete(memory_id)
	return {"ok": True}

