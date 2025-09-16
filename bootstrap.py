# bootstrap.py — auto-creates all project files with correct content
import os
from pathlib import Path

root = Path.cwd()
(root / "app").mkdir(exist_ok=True)
(root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

files = {
    "app/__init__.py": "",
    "app/config.py": "print('config placeholder')\n",
    "app/db.py": "print('db placeholder')\n",
    "app/models.py": "print('models placeholder')\n",
    "app/utils.py": "print('utils placeholder')\n",
    "app/parser.py": "print('parser placeholder')\n",
    "app/scraper.py": "print('scraper placeholder')\n",
    "app/alerts.py": "print('alerts placeholder')\n",
    "app/logic.py": "print('logic placeholder')\n",
    "app/scheduler.py": "print('scheduler placeholder')\n",
    "add_product.py": "print('add_product placeholder')\n",
    "run_once.py": "print('run_once placeholder')\n",
    ".github/workflows/price-watch.yml": "name: placeholder\n",
}

for path, content in files.items():
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

print("✅ All placeholder files created. Now you can edit them in Notepad or VS Code.")
