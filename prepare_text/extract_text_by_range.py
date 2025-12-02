import os
import re  # 导入正则表达式库，用于更可靠地解析序号


def extract_text_by_range(input_filepath, start_num, end_num, encoding='utf-8', output_filepath=None):
    """
    根据行开头的序号范围，抽取文件中的部分文本，并保持原有的“○[序号]”前缀。

    :param input_filepath: str, 带有序号的前缀的txt文件路径。
    :param start_num: int, 抽取的起始序号（包含）。
    :param end_num: int, 抽取的结束序号（包含）。
    :param encoding: str, 文件编码，默认为 'utf-8'。
    :param output_filepath: str, 可选，抽取结果保存的文件路径。如果为 None，则只打印到控制台。
    :return: list, 抽取出的文本列表。
    """

    extracted_lines = []

    try:
        # 1. 读取文件内容
        with open(input_filepath, 'r', encoding=encoding) as infile:
            for line in infile:
                # 保留原始行，因为我们需要它来输出完整的文本
                original_line = line
                stripped_line = line.strip()

                # 跳过空行
                if not stripped_line:
                    continue

                # 2. 解析行号
                if stripped_line.startswith('○'):
                    # 尝试用正则表达式匹配：○ 后面紧跟着的数字
                    match = re.match(r'○(\d+)', stripped_line)

                    if match:
                        try:
                            # 提取匹配到的序号
                            num_str = match.group(1)
                            current_num = int(num_str)

                            # **核心修改点：**
                            # 3. 检查序号是否在范围内
                            if start_num <= current_num <= end_num:
                                # **不再提取子字符串，而是直接添加原始行内容。**
                                # 注意：如果原始行带有换行符，我们不需要额外添加 \n
                                extracted_lines.append(original_line.rstrip('\n'))  # 移除行末换行符，后续统一添加

                            # 优化：如果当前序号已经超过结束范围，就停止读取
                            if current_num > end_num:
                                break

                        except ValueError:
                            continue
                        except Exception:
                            continue

        # 4. 输出结果
        if not extracted_lines:
            print(f"在 {input_filepath} 中未找到序号范围 {start_num}-{end_num} 内的文本。")
            return []

        if output_filepath:
            # 写入到文件
            with open(output_filepath, 'w', encoding=encoding) as outfile:
                # 每行末尾添加换行符，以便写入文件
                outfile.writelines([line + '\n' for line in extracted_lines])
            print(f"\n文本抽取成功！")
            print(f"抽取范围: {start_num}-{end_num}")
            print(f"输出文件: {output_filepath}")
        else:
            # 打印到控制台
            print(f"\n--- 抽取结果 (序号 {start_num}-{end_num}) ---")
            for line in extracted_lines:
                print(line)
            print("--------------------------------------")

        return extracted_lines

    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_filepath}'")
        return []
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return []


# ==========================================================
# 使用示例：使用您的实际路径和范围
# ==========================================================

# 1. 您的实际文件路径
input_file_with_numbers = r'/Users/luckpuppy/Desktop/扩充训练集/0926结构化训练集/2-人工/Train_nonriots_非动乱-人工遍历.txt'

# 2. 只需要修改起始和结束序号
start = 701
end = 800

# 3. 指定输出文件路径
output_template = r'/Users/luckpuppy/Desktop/抽取结果_{start}_{end}_带序号.txt'  # 建议修改文件名，以区分上次的输出

output_file = output_template.format(start=start, end=end)

# 调用函数（保存到文件）
extract_text_by_range(input_file_with_numbers, start, end,
                      output_filepath=output_file)