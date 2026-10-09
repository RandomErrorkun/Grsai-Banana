# -*- coding: utf-8 -*-
"""将 grsai_history.db 的 history_tasks 表导出为制表符分隔的 grsai_history.csv。

- 列与 core/history_manager.py 中 history_tasks 表一致
- UTF-8 with BOM 编码，Excel 双击打开中文不乱码
- 字段内的制表符/换行/回车转义为 \t \n \r，保证一条记录占一行
- NULL 输出为空字符串；ref_images / ref_audios 保留原始 JSON 文本
"""

import sqlite3

DB_FILE = "grsai_history.db"
OUT_FILE = "grsai_history.csv"


def escape_field(value):
    if value is None:
        return ""
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def main():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(history_tasks)")]
        rows = conn.execute(
            "SELECT * FROM history_tasks ORDER BY created_at DESC, id DESC"
        ).fetchall()
    finally:
        conn.close()

    with open(OUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\t".join(columns) + "\n")
        for row in rows:
            f.write("\t".join(escape_field(row[col]) for col in columns) + "\n")

    print(f"exported {len(rows)} rows -> {OUT_FILE}")


if __name__ == "__main__":
    main()
