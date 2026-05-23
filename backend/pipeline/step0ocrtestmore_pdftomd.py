from .imports import *

def batch_process_with_filter(input_folder, output_base_dir=rf"./md_output", 
                             recursive=True, file_filter=None, skip_existing=True):
    """
    带文件过滤的批量处理
    
    参数:
    - input_folder: 输入文件夹路径
    - output_base_dir: 输出基础目录
    - recursive: 是否递归搜索子文件夹
    - file_filter: 文件过滤函数，接受文件名作为参数，返回True/False
    - skip_existing: 若输出md已存在，是否跳过
    """
    
    pipeline = PPStructureV3(
        use_doc_orientation_classify=False, 
        use_doc_unwarping=False, 
        use_textline_orientation=False,
        use_seal_recognition=False, 
        use_formula_recognition=True, 
        use_chart_recognition=True,
        use_region_detection=False, 
        use_table_recognition=True,
        device='gpu'
    )
    
    Path(output_base_dir).mkdir(parents=True, exist_ok=True)
    
    # 查找PDF文件
    input_path = Path(input_folder)
    pdf_files = list(input_path.rglob("*.pdf"))
    if recursive:
        pdf_files = list(input_path.rglob("*.pdf"))
    else:
        pdf_files = list(input_path.glob("*.pdf"))
    
    # 应用文件过滤器
    if file_filter:
        pdf_files = [f for f in pdf_files if file_filter(f.name)]
    
    if not pdf_files:
        print(f"在文件夹 {input_folder} 中未找到符合条件的PDF文件")
        return
    
    print(f"找到 {len(pdf_files)} 个符合条件的PDF文件")
    
    success_count = 0
    skip_count = 0
    for i, pdf_file in enumerate(pdf_files, 1):
        file_stem = pdf_file.stem
        mkd_file_path = Path(output_base_dir) / f"{file_stem}.md"
        
        # ✅ 关键新增：已存在则跳过
        if skip_existing and mkd_file_path.exists():
            print(f"跳过 {i}/{len(pdf_files)}: {pdf_file.name}（已存在）")
            skip_count += 1
            continue

        print(f"正在处理第 {i}/{len(pdf_files)} 个文件: {pdf_file}")
        
        try:   
            # 处理文档
            output = pipeline.predict(input=str(pdf_file))
            
            # 提取内容
            markdown_list = []
            # markdown_images = []
            
            for res in output:
                md_info = res.markdown
                markdown_list.append(md_info)
                # markdown_images.append(md_info.get("markdown_images", {}))
            
            # 合并markdown
            markdown_result = pipeline.concatenate_markdown_pages(markdown_list)
            
            # ✅ 关键修复点：确保写入的是 str
            if hasattr(markdown_result, "to_markdown"):
                markdown_text = markdown_result.to_markdown()
            else:
                markdown_text = str(markdown_result)
                
            # 保存文件
            # mkd_file_path = output_path / f"{file_stem}.md"
            mkd_file_path = Path(output_base_dir) / f"{file_stem}.md"
            with open(mkd_file_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
            print(f"  - Markdown文件已保存: {mkd_file_path}")
            
            # # 保存图片
            # image_count = 0
            # for item in markdown_images:
            #     if item:
            #         for path, image in item.items():
            #             file_path = output_path / path
            #             file_path.parent.mkdir(parents=True, exist_ok=True)
            #             image.save(file_path)
            #             image_count += 1
            
            # if image_count > 0:
            #     print(f"  - 已保存 {image_count} 张图片")
            
            success_count += 1
            
        except Exception as e:
            print(f"  - 处理失败: {e}")
            
        # finally:
        #     # ✅ 防止显存累积爆炸
        #     gc.collect()
        #     paddle.device.cuda.empty_cache()
            
        print("-" * 60)
    
    print(f"批量处理完成！成功处理 {success_count}/{len(pdf_files)} 个文件")

# # 使用示例
# if __name__ == "__main__": 
#     input_folder = rf"/data/wangsiqi/work/LumberChunker/3周目/allpdf_havechecked/test"
#     output_base_dir=rf"/data/wangsiqi/work/LumberChunker/3周目/all_md/test"
#     # 示例1：处理所有PDF文件
#     batch_process_with_filter(input_folder, output_base_dir)
    