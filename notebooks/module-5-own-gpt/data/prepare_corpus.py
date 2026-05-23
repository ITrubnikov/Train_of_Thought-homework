"""
prepare_corpus.py — объединяет несколько txt-файлов в один pushkin.txt.

Использование:
    python prepare_corpus.py raw_dir/*.txt -o pushkin.txt

Что делает:
- Читает все указанные файлы в UTF-8 (с попыткой fallback на windows-1251).
- Убирает строки-разделители Wikisource / az.lib.ru ("===", "---", "[править]").
- Схлопывает множественные пустые строки в одну.
- Пишет результат в pushkin.txt.

Не делает чистку от HTML-разметки — для этого используй bleach или
mwparserfromhell отдельно.
"""

import argparse
import re
import sys
from pathlib import Path


JUNK_LINE = re.compile(r"^\s*([=-]{3,}|\[править\].*|<.*>)\s*$")
MULTIBLANK = re.compile(r"\n{3,}")


def read_txt(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8", "windows-1251", "koi8-r"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"не удалось определить кодировку: {path}")


def clean(text: str) -> str:
    lines = [ln for ln in text.splitlines() if not JUNK_LINE.match(ln)]
    return MULTIBLANK.sub("\n\n", "\n".join(lines)).strip() + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", type=Path, help="входные txt-файлы")
    p.add_argument("-o", "--out", default="pushkin.txt", type=Path)
    args = p.parse_args()

    chunks = []
    for path in args.inputs:
        if not path.exists():
            print(f"пропускаю (нет файла): {path}", file=sys.stderr)
            continue
        chunks.append(clean(read_txt(path)))
        print(f"+ {path} ({path.stat().st_size:,} bytes)", file=sys.stderr)

    if not chunks:
        sys.exit("нет валидных входных файлов")

    args.out.write_text("\n\n".join(chunks), encoding="utf-8")
    print(f"\n→ {args.out} ({args.out.stat().st_size:,} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
