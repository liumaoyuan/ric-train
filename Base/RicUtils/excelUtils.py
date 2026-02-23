import io
from typing import List, Optional, Union
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def dict_list_to_excel(
    data: List[dict],
    output_path: Optional[str] = None,
    sheet_name: str = "Sheet1"
) -> Union[bytes, None]:
    """
    将 List[dict] 数据转换为 Excel 文件

    Args:
        data: 字典列表，每个字典代表一行数据
        output_path: 输出文件路径，如果为 None 则返回字节流（用于 FastAPI 接口）
        sheet_name: 工作表名称，默认为 "Sheet1"

    Returns:
        如果 output_path 为 None，返回 Excel 文件的字节流（bytes）
        如果 output_path 有值，保存到文件并返回 None

    Example:
        # 示例1：直接返回字节流（用于 FastAPI）
        data = [
            {"姓名": "张三", "年龄": 25, "城市": "北京"},
            {"姓名": "李四", "年龄": 30, "城市": "上海"}
        ]
        excel_bytes = dict_list_to_excel(data)
        with open('output.xlsx', 'wb') as f:
            f.write(excel_bytes)

        # 示例2：保存到文件
        dict_list_to_excel(data, output_path='output.xlsx')

        # 示例3：在 FastAPI 中使用
        @app.get("/export")
        async def export_data():
            data = query_data()  # 查询数据
            excel_bytes = dict_list_to_excel(data)
            return Response(
                content=excel_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=data.xlsx"}
            )
    """
    if not data:
        raise ValueError("数据不能为空")

    # 创建工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    # 获取所有字段名（取所有字典的并集，保证所有列都包含）
    all_headers = set()
    for row in data:
        all_headers.update(row.keys())
    headers = list(all_headers)

    # 设置表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    # 写入表头
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    # 写入数据
    for row_idx, row_data in enumerate(data, start=2):
        for col_idx, header in enumerate(headers, 1):
            value = row_data.get(header, "")
            ws.cell(row=row_idx, column=col_idx, value=value)

    # 自动调整列宽
    for col_idx, header in enumerate(headers, 1):
        max_length = len(str(header))
        for row_data in data:
            value = str(row_data.get(header, ""))
            # 考虑中文字符，长度乘以1.5
            length = len(value)
            # 计算实际显示长度（中文字符占更多宽度）
            actual_length = sum(1.5 if '\u4e00' <= char <= '\u9fff' else 1 for char in value)
            max_length = max(max_length, actual_length)
        ws.column_dimensions[chr(64 + col_idx)].width = min(max_length + 2, 50)

    # 保存到 BytesIO 或文件
    if output_path:
        wb.save(output_path)
        return None
    else:
        # 保存到内存中的 BytesIO 对象
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()


def dict_list_to_excel_stream(data: List[dict], sheet_name: str = "Sheet1") -> io.BytesIO:
    """
    将 List[dict] 数据转换为 Excel 文件流（返回 BytesIO 对象）

    Args:
        data: 字典列表，每个字典代表一行数据
        sheet_name: 工作表名称，默认为 "Sheet1"

    Returns:
        BytesIO 对象，可直接用于 FastAPI 的 FileResponse 或 StreamingResponse

    Example:
        @app.get("/export")
        async def export_data():
            data = query_data()  # 查询数据
            excel_stream = dict_list_to_excel_stream(data)
            return StreamingResponse(
                io.BytesIO(excel_stream.getvalue()),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=data.xlsx"}
            )
    """
    excel_bytes = dict_list_to_excel(data, sheet_name=sheet_name)
    return io.BytesIO(excel_bytes)
