listArr = []


def read_and_print_file(fileName: str):
    try:
        with open(fileName, 'r', encoding='utf-8') as file:
            # 逐行读取并输出
            for line in file:
                listArr.append(line.strip())
                print(line.strip())  # 使用 strip() 去掉每行末尾的换行符
    except FileNotFoundError:
        print(f"File '{fileName}' not found.")
    except IOError as e:
        print(f"An error occurred while reading the file: {e}")


# 使用示例
filename = 'demo.txt'
read_and_print_file(filename)
print(listArr)
