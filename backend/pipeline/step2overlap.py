from .imports import *

def overlap_chunks(chunks, overlap_size=150):
    overlapped_chunks = []
    prev_tail = ""

    for chunk in chunks:
        if not isinstance(chunk, str):
            chunk = ""

        new_chunk = prev_tail + chunk
        overlapped_chunks.append(new_chunk)

        if len(chunk) > overlap_size:
            prev_tail = chunk[-overlap_size:]
        else:
            prev_tail = chunk

    return overlapped_chunks
 
# # ========= 路径 =========
# chunk_dir = Path("/data/wangsiqi/work/LumberChunker/md_sample2/chunk")
# overlap_dir = chunk_dir / "overlap"
# overlap_dir.mkdir(exist_ok=True)
 
def process_single_overlap_excel(old_chunk_file, overlap_dir, overlap_size=150):
    print(f"🔄 overlap 处理中：{old_chunk_file.name}")

    new_chunk_file = overlap_dir / old_chunk_file.name.replace(".xlsx", "_newchunk.xlsx")

    # 断点保护
    if new_chunk_file.exists():
        print(f"⚠️ 已存在，跳过：{new_chunk_file.name}")
        return

    df_old = pd.read_excel(old_chunk_file)

    if "Chunk" not in df_old.columns:
        print(f"❌ Chunk 列不存在，跳过：{old_chunk_file.name}")
        return

    original_chunks = df_old["Chunk"].tolist()
    overlapped_chunks = overlap_chunks(original_chunks, overlap_size=overlap_size)

    df_new = df_old.copy()
    df_new["Chunk"] = overlapped_chunks
    df_new.to_excel(new_chunk_file, index=False)

    print(f"✅ overlap 完成 → {new_chunk_file}")

def batch_overlap_excels(chunk_dir, overlap_dir=None, overlap_size=150):
    if overlap_dir is None:
        overlap_dir = chunk_dir / "overlap"
    overlap_dir.mkdir(parents=True,exist_ok=True)

    for old_chunk_file in sorted(chunk_dir.glob("Chunks_-_*.xlsx")):
        process_single_overlap_excel(old_chunk_file, overlap_dir, overlap_size)
