import os
from pathlib import Path


def get_db_path() -> Path:
	custom = os.environ.get("ASSISTANT_DB_PATH")
	if custom:
		return Path(custom).expanduser()
	base = Path.home() / ".myassistant"
	base.mkdir(parents=True, exist_ok=True)
	return base / "memories.db"

