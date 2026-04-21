"""
build_hierarchical.py
=====================
Xây dựng Hierarchical Chunking (Parent-Document Retriever) cho RAG.

Chiến lược: KHÔNG lưu 2 collection riêng biệt.
Thay vào đó: thêm trường "full_dieu_text" vào PAYLOAD của mỗi child chunk.
→ Khi retrieve child, lấy full_dieu_text đưa vào LLM ngay, không cần round-trip thêm.
→ Đơn giản, ít thay đổi pipeline, phù hợp deadline đồ án.

Với điều quá dài (> 4000 ký tự): cap parent ở 4000 ký tự + note "[Xem thêm...]"
để tránh làm LLM context quá lớn.

Cách dùng:
    python build_hierarchical.py \
        --chunks data/law_chunks.jsonl \
        --excel  data/law_data_output.xlsx \
        --output data/law_chunks_hier.jsonl
"""

import json
import argparse
import logging
import hashlib
import openpyxl
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

PARENT_MAX_LEN = 4000   # cap độ dài full_dieu_text đưa vào LLM context
EXCEL_MAX_LEN  = 32767  # flag Excel truncate


def load_full_dieu(excel_path: str) -> dict:
    """
    Đọc law_data_output.xlsx → dict {(source_file, dieu_so): noi_dung_dieu_day_du}
    Đây là "parent" - toàn bộ nội dung điều chưa bị cắt.
    """
    log.info(f"📖 Đọc parent data từ {excel_path}...")
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb["Dữ liệu luật"]
    rows = list(ws.values)
    headers = [str(h).strip() if h else "" for h in rows[0]]
    hi = {h: i for i, h in enumerate(headers)}

    parent_map = {}
    truncated_count = 0

    for row in rows[1:]:
        sf  = str(row[hi.get("Source File", 0)] or "").strip()
        ds  = str(row[hi.get("Điều số", 0)]     or "").strip()
        nd  = str(row[hi.get("Nội dung điều", 0)] or "").strip()
        if not sf or not ds or not nd:
            continue

        is_truncated = len(nd) >= EXCEL_MAX_LEN
        if is_truncated:
            truncated_count += 1

        key = (sf, ds)
        # Nếu trùng key (điều số bị duplicate từ parse sai) → giữ cái đầu tiên
        if key not in parent_map:
            parent_map[key] = {
                "noi_dung": nd,
                "is_truncated": is_truncated,
            }

    log.info(f"  ✅ {len(parent_map):,} điều | {truncated_count} bị truncate Excel")
    return parent_map


def build_full_dieu_text(nd: str, max_len: int, meta: dict) -> str:
    """
    Tạo full_dieu_text cho LLM context.
    Với điều dài > max_len: truncate + ghi chú.
    """
    if len(nd) <= max_len:
        return nd

    # Truncate tại câu hoàn chỉnh gần nhất
    truncated = nd[:max_len]
    last_period = max(
        truncated.rfind(". "),
        truncated.rfind(".\n"),
        truncated.rfind("; "),
    )
    if last_period > max_len * 0.7:
        truncated = truncated[:last_period + 1]

    source = meta.get("source_file", "")
    dieu_so = meta.get("dieu_so", "")
    return (
        truncated
        + f"\n...[Nội dung còn lại của Điều {dieu_so} ({source}) quá dài "
        f"({len(nd):,} ký tự), đã rút gọn. Xem đầy đủ trong văn bản gốc.]"
    )


def enrich_chunks(chunks: list, parent_map: dict, parent_max_len: int) -> list:
    """
    Thêm trường vào mỗi child chunk:
      - full_dieu_text : toàn bộ nội dung điều (capped) → đưa vào LLM prompt
      - parent_dieu_id : hash của (source_file, dieu_so) → để group chunks
      - is_parent_truncated : True nếu điều gốc bị cắt trong Excel
    """
    log.info(f"🔗 Enrich {len(chunks):,} chunks với parent data...")

    enriched = []
    missing  = 0
    stat_dieu_sizes = defaultdict(int)

    for chunk in chunks:
        p = chunk.get("payload", {})
        sf = p.get("source_file", "")
        ds = p.get("dieu_so", "")
        key = (sf, ds)

        parent_info = parent_map.get(key)
        if parent_info is None:
            missing += 1
            full_text = p.get("noi_dung_chunk", "")  # fallback: chỉ dùng chunk hiện tại
            is_trunc  = False
        else:
            nd = parent_info["noi_dung"]
            full_text = build_full_dieu_text(nd, parent_max_len, p)
            is_trunc  = parent_info["is_truncated"]
            stat_dieu_sizes[len(nd)] += 1

        # Parent ID: dùng để group tất cả children cùng điều
        parent_id = hashlib.md5(f"{sf}_{ds}".encode()).hexdigest()[:12]

        new_chunk = dict(chunk)
        new_chunk["payload"] = {
            **p,
            "full_dieu_text":     full_text,    # ← KEY FIELD: LLM sẽ dùng cái này
            "parent_dieu_id":     parent_id,    # ← group chunks cùng điều
            "is_parent_truncated": is_trunc,    # ← cảnh báo nếu parent bị cắt
        }
        enriched.append(new_chunk)

    if missing:
        log.warning(f"  ⚠ {missing} chunks không tìm được parent (dùng fallback)")

    # Thống kê
    sizes = list(stat_dieu_sizes.keys())
    if sizes:
        sizes.sort()
        n = len(sizes)
        log.info(f"  📊 Parent size: P50={sizes[n//2]:,} P90={sizes[int(n*0.9)]:,} Max={max(sizes):,} ký tự")
        capped = sum(1 for s in sizes if s > parent_max_len)
        log.info(f"  📊 Điều bị cap ({parent_max_len:,} ký tự): {capped}")

    log.info(f"  ✅ Enrich hoàn tất: {len(enriched):,} chunks")
    return enriched


def validate_output(chunks: list):
    """Kiểm tra nhanh chất lượng sau enrich."""
    log.info("\n🔍 Validation:")
    no_full  = sum(1 for c in chunks if not c["payload"].get("full_dieu_text", "").strip())
    no_pid   = sum(1 for c in chunks if not c["payload"].get("parent_dieu_id", "").strip())
    trunc    = sum(1 for c in chunks if c["payload"].get("is_parent_truncated"))
    full_lens = [len(c["payload"].get("full_dieu_text", "")) for c in chunks]

    print(f"  Thiếu full_dieu_text: {no_full}")
    print(f"  Thiếu parent_dieu_id: {no_pid}")
    print(f"  Chunk có parent bị truncate Excel: {trunc}")
    print(f"  full_dieu_text avg={int(sum(full_lens)/len(full_lens))} "
          f"P90={sorted(full_lens)[int(len(full_lens)*0.9)]:,} "
          f"Max={max(full_lens):,} ký tự")
    print(f"  → Tất cả {'✅ OK' if no_full == 0 and no_pid == 0 else '⚠ CÓ VẤN ĐỀ'}")


def main():
    parser = argparse.ArgumentParser(
        description="Thêm full_dieu_text (parent) vào payload của mỗi chunk"
    )
    parser.add_argument("--chunks",  "-c", default="data/law_chunks.jsonl",
                        help="File JSONL child chunks từ smart_chunker.py")
    parser.add_argument("--excel",   "-e", default="data/law_data_output.xlsx",
                        help="File Excel chứa nội dung điều đầy đủ")
    parser.add_argument("--output",  "-o", default="data/law_chunks_hier.jsonl",
                        help="Output file JSONL đã enrich")
    parser.add_argument("--parent_max_len", type=int, default=PARENT_MAX_LEN,
                        help=f"Độ dài tối đa full_dieu_text (mặc định {PARENT_MAX_LEN})")
    args = parser.parse_args()

    # Kiểm tra input
    for p in [args.chunks, args.excel]:
        if not Path(p).exists():
            log.error(f"Không tìm thấy: {p}")
            return

    # Load parent data
    parent_map = load_full_dieu(args.excel)

    # Load child chunks
    log.info(f"📂 Đọc chunks từ {args.chunks}...")
    chunks = []
    with open(args.chunks, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    log.info(f"  ✅ {len(chunks):,} chunks")

    # Enrich
    enriched = enrich_chunks(chunks, parent_map, args.parent_max_len)

    # Validate
    validate_output(enriched)

    # Xuất
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for chunk in enriched:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    log.info(f"\n✅ Đã xuất: {out}")
    log.info(f"   {len(enriched):,} chunks với full_dieu_text trong payload")
    log.info(f"\n📤 Giao cho Phú: {out}")
    log.info("   Phú dùng file này thay thế law_chunks.jsonl để embed vào Qdrant")
    log.info("   Khi retrieve: lấy payload['full_dieu_text'] đưa vào LLM prompt")


if __name__ == "__main__":
    main()