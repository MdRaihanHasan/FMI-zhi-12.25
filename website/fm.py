# this is fm.py Created by Zhi 2024.9
import os
import random
import string
import time
import subprocess
from werkzeug.utils import secure_filename

ROOT_METADATA_PATH = os.path.join('metadata', 'root.lst.cpabe')
METADATA_FOLDER = 'metadata'

# 修改密钥文件路径为实际路径
PUB_KEY = 'website/keys/pub_key'
MASTER_KEY = 'website/keys/master_key'  # 虽然不直接使用，但记录一下
PRIVATE_KEYS = {
    'administrator': 'website/keys/private_administrator_key',
    'expert': 'website/keys/private_expert_key',
    'contributor': 'website/keys/private_contributor_key'
}


def encrypt_file(file_path, policy):
    """使用 cpabe-enc 加密文件"""
    try:
        # 加密后的文件会自动添加.cpabe后缀
        # 构建加密命令
        cmd = ['cpabe-enc', PUB_KEY, file_path, policy]
        print(f"执行加密命令: {' '.join(cmd)}")

        # 执行加密命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"加密错误: {result.stderr}")
            return None

        encrypted_path = file_path + '.cpabe'
        if os.path.exists(encrypted_path):
            print(f"文件加密成功: {encrypted_path}")
            return encrypted_path
        else:
            print(f"加密文件未找到: {encrypted_path}")
            return None

    except Exception as e:
        print(f"加密过程错误: {str(e)}")
        return None


def decrypt_file(encrypted_path, role, output_path=None):
    """使用 cpabe-dec 解密文件"""
    try:
        # 获取私钥路径
        private_key = os.path.abspath(f'website/keys/private_{role}_key')
        pub_key = os.path.abspath('website/keys/pub_key')

        # 确保输入文件存在
        if not os.path.exists(encrypted_path):
            print(f"加密文件不存在: {encrypted_path}")
            return None

        # 如果没有指定输出路径，创建一个临时路径
        if output_path is None:
            output_path = encrypted_path.replace('.cpabe', '.dec')

        # 创建加密文件的副本
        temp_encrypted = f"{encrypted_path}.temp"
        subprocess.run(['cp', encrypted_path, temp_encrypted])

        try:
            # 构建解密命令，使用临时文件作为输入
            cmd = ['cpabe-dec', pub_key, private_key, temp_encrypted, '-o', output_path]
            print(f"执行解密命令: {' '.join(cmd)}")

            # 执行解密命令
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"解密错误: {result.stderr}")
                return None

            if os.path.exists(output_path):
                print(f"文件解密成功: {output_path}")
                return output_path
            else:
                print(f"解密文件未找到: {output_path}")
                return None

        finally:
            # 清理临时加密文件
            if os.path.exists(temp_encrypted):
                os.remove(temp_encrypted)

    except Exception as e:
        print(f"解密过程错误: {str(e)}")
        return None


def initialize_metadata_structure():
    """初始化存储元数据的目录结构"""
    os.makedirs(METADATA_FOLDER, exist_ok=True)
    root_metadata_path = os.path.join(METADATA_FOLDER, 'root.lst')
    if not os.path.exists(root_metadata_path):
        with open(root_metadata_path, 'w') as f:
            f.write("METADATA FILE STRUCTURE\n=====================\n\n")

def get_metadata_path(folder_name):
    """返回指定目录对应的元数据文件路径"""
    return os.path.join(METADATA_FOLDER, f"{folder_name}.lst")


def get_headers_and_blocks(metadata_file_path):
    """从元数据文件中提取头部和块的内容"""
    if not os.path.exists(metadata_file_path):
        return [], []
    try:
        with open(metadata_file_path, 'r') as f:
            content = f.read()
        if not content.strip():
            return [], []

        parts = content.split("BLOCK\n=====\n")
        headers_section = parts[0]
        blocks = parts[1:] if len(parts) > 1 else []
        headers = [line.strip() for line in headers_section.split('\n')
                   if line.strip() and line.strip().startswith('HEADER:')]
        return headers, blocks
    except Exception as e:
        print(f"读取元数据文件错误: {e}")
        return [], []


def recalculate_header_ranges(headers, blocks):
    """
    Recalculate header ranges with proper error handling and dictionary initialization
    """
    current_byte = 0
    new_headers = []
    
    # Initialize blocks_by_attr safely
    blocks_by_attr = {}
    for header in headers:
        try:
            attr = header.split(':')[1].split('(')[0].strip()
            blocks_by_attr[attr] = []
        except (IndexError, ValueError):
            continue
    
    # Process blocks
    for block in blocks:
        if not block.strip():
            continue
        
        try:
            lines = block.split('\n')
            attr_line = next((line for line in lines if line.startswith('Attribute:')), None)
            if attr_line:
                attr = attr_line.split(':', 1)[1].strip()
                if attr not in blocks_by_attr:
                    blocks_by_attr[attr] = []
                blocks_by_attr[attr].append(block)
        except Exception as e:
            print(f"Error processing block: {e}")
            continue
    
    # Generate new headers
    for attr, attr_blocks in blocks_by_attr.items():
        header_line = f"HEADER: {attr} ({current_byte}, {len(attr_blocks)})"
        new_headers.append(header_line)
        current_byte += len(attr_blocks)
    
    return new_headers, list(blocks_by_attr.values())


def update_metadata_file(metadata_file_path, attr, block_content):
    """更新元数据文件"""
    temp_path = f"{metadata_file_path}.tmp"
    try:
        # 获取现有内容
        headers, blocks = get_headers_and_blocks(metadata_file_path)

        # 确保块内容以换行结束
        block_content = block_content.strip() + '\n'
        blocks.append(block_content)

        # 写入临时文件
        with open(temp_path, 'w') as f:
            # 写入头部
            if headers:
                f.write('\n'.join(headers))
            f.write('\n\nBLOCK\n=====\n')

            # 写入块
            for block in blocks:
                f.write(block.strip() + '\nBLOCK\n=====\n')

        # 原子替换
        os.replace(temp_path, metadata_file_path)
        return True

    except Exception as e:
        print(f"更新元数据文件错误: {str(e)}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False


def secure_and_save_file(file, folder_name, role):
    """
    处理上传的文件：
    1. 生成随机文件名
    2. 创建文件夹
    3. 保存文件
    4. 加密文件
    5. 删除原始文件
    """
    temp_path = None
    try:
        # 生成安全的文件名和路径
        filename = secure_filename(file.filename)
        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        folder_path = os.path.join('root', secure_filename(folder_name))
        os.makedirs(folder_path, exist_ok=True)

        # 保存原始文件
        temp_path = os.path.join(folder_path, random_name)
        file.save(temp_path)
        print(f"文件已保存到临时位置: {temp_path}")

        # 根据角色设置访问策略
        if role == 'administrator':
            policy = 'administrator'
        elif role == 'expert':
            policy = 'expert or administrator'
        else:  # contributor
            policy = 'contributor or expert or administrator'

        print(f"使用访问策略: {policy}")

        # 加密文件
        encrypted_path = encrypt_file(temp_path, policy)

        if encrypted_path:
            # 删除原始文件
            os.remove(temp_path)
            print(f"临时文件已删除: {temp_path}")
            return filename, random_name, encrypted_path

        raise Exception("加密失败")

    except Exception as e:
        print(f"文件处理错误: {str(e)}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"清理临时文件: {temp_path}")
        return None, None, None

def create_folder_metadata(folder_name, attribute):
    """为特定目录创建元数据文件"""
    folder_metadata_path = get_metadata_path(folder_name)
    try:
        initialize_metadata_structure()
        if not os.path.exists(folder_metadata_path):
            with open(folder_metadata_path, 'w') as f:
                f.write(f"Folder: {folder_name}\n")
                f.write(f"Attribute: {attribute}\n")
                f.write("\nBLOCK\n=====\n")
        return folder_metadata_path
    except Exception as e:
        print(f"创建文件夹元数据错误: {str(e)}")
        return None

def search_metadata_for_keywords(metadata_path, keywords):
    """在元数据文件中搜索关键词"""
    results = []
    if not os.path.exists(metadata_path):
        return results
    try:
        with open(metadata_path, 'r') as f:
            content = f.read()
        blocks = content.split("BLOCK\n=====\n")
        for block in blocks[1:]:  # 跳过头部部分
            if block.strip() and any(keyword.lower() in block.lower()
                                   for keyword in keywords.split()):
                # 解析块为结构化格式
                block_data = {}
                for line in block.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        block_data[key.strip()] = value.strip()
                if block_data:
                    # 添加文件状态信息
                    if 'Path' in block_data:
                        encrypted_path = block_data['Path']
                        block_data['Encrypted'] = os.path.exists(encrypted_path)
                        decrypted_path = encrypted_path.replace('.cpabe', '')
                        block_data['Decrypted'] = os.path.exists(decrypted_path)
                    results.append(block_data)
    except Exception as e:
        print(f"搜索元数据错误: {e}")
    return results

