import os


def add_prefix_to_txt(input_filepath, output_filepath=None, encoding='utf-8'):
    """
    为txt文件中的每条非空文本行开头加上“○”和序号。

    :param input_filepath: str, 待处理的txt文件路径。
    :param output_filepath: str, 可选，处理结果保存的文件路径。
                            如果为 None，则默认在输入文件路径前添加 "_numbered"。
    :param encoding: str, 文件编码，默认为 'utf-8'。
    """

    # 确定输出文件路径
    if output_filepath is None:
        base, ext = os.path.splitext(input_filepath)
        output_filepath = base + "_numbered" + ext

    processed_lines = []
    line_number = 1

    try:
        # 1. 读取文件内容
        with open(input_filepath, 'r', encoding=encoding) as infile:
            for line in infile:
                # 移除行首和行尾的空白字符（包括换行符）
                stripped_line = line.strip()

                # 检查行是否为空（如果文件中有空行，可以选择跳过或为它们编号）
                if stripped_line:
                    # 2. 添加“○”和序号
                    # 使用 f-string 格式化，序号后跟一个空格或分隔符，然后是原文本。
                    # 您也可以调整 {line_number} 的格式，例如 {line_number:03} 表示三位数字，不足补0
                    # 移除句号和空格（`. `）
                    new_line = f"○{line_number}{stripped_line}"
                    processed_lines.append(new_line + '\n')  # 重新添加换行符
                    line_number += 1
                elif line.endswith('\n'):
                    # 如果是包含换行符的空行，则保留空行，不编号
                    processed_lines.append('\n')
                # 否则，如果是不包含换行符的空行（如文件末尾），则忽略

        # 3. 写入处理后的内容到新文件
        with open(output_filepath, 'w', encoding=encoding) as outfile:
            outfile.writelines(processed_lines)

        print(f"文件处理成功！")
        print(f"输入文件: {input_filepath}")
        print(f"输出文件: {output_filepath}")

    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_filepath}'")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")


# ==========================================================
# 使用示例：每次修改下方路径即可对新文件进行处理
# ==========================================================

# 仅修改这个路径即可
input_file = r'/Users/luckpuppy/Desktop/扩充训练集/0926结构化训练集/4/annotation/Train_nonriots_cleaned.txt'

# 可以选择指定输出文件路径，如果不指定，将自动生成一个名称
# output_file = r'/Users/your_username/Desktop/已处理文本_带序号.txt'

# 调用函数
add_prefix_to_txt(input_file)
# add_prefix_to_txt(input_file, output_filepath=output_file) # 如果指定了输出路径，则使用此行