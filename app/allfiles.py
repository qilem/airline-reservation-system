import os


def list_files(start_path, indent=''):
    """
    递归列出文件夹中的所有文件和子文件夹

    参数:
    start_path: 起始目录的路径
    indent: 缩进字符串,用于显示层级结构
    """
    # 确保路径存在
    if not os.path.exists(start_path):
        print(f"路径不存在: {start_path}")
        return

    # 获取当前目录下的所有文件和文件夹
    try:
        items = os.listdir(start_path)
    except PermissionError:
        print(f"{indent}[访问被拒绝] {start_path}")
        return

    # 分别存储文件和文件夹
    files = []
    dirs = []

    for item in items:
        full_path = os.path.join(start_path, item)
        if os.path.isfile(full_path):
            files.append(item)
        else:
            dirs.append(item)

    # 先打印所有文件
    for f in sorted(files):
        print(f"{indent}├── {f}")

    # 再打印所有文件夹及其内容
    for i, d in enumerate(sorted(dirs)):
        is_last = (i == len(dirs) - 1)
        print(f"{indent}{'└── ' if is_last else '├── '}{d}/")

        # 递归处理子文件夹
        next_indent = indent + ('    ' if is_last else '│   ')
        full_path = os.path.join(start_path, d)
        list_files(full_path, next_indent)


# 使用示例
if __name__ == "__main__":
    folder_path = 'E:\database\\air_ticket'
    print(f"\n{os.path.basename(folder_path)}/")
    list_files(folder_path)