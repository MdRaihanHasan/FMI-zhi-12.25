# Created by Zhi 2024.9
from charm.toolbox.pairinggroup import PairingGroup
from charm.schemes.abenc.abenc_bsw07 import CPabe_BSW07
from charm.core.engine.util import objectToBytes
import os
def save_key(key, filepath, group):
   """安全地保存密钥到二进制文件"""
   try:
       # 序列化密钥为字节
       key_bytes = objectToBytes(key, group)
       
       # 创建临时文件
       temp_path = f"{filepath}.tmp"
       with open(temp_path, 'wb') as f:
           f.write(key_bytes)
       
       # 原子性替换
       os.replace(temp_path, filepath)
       print(f"成功保存密钥到 {filepath}")
       return True
       
   except Exception as e:
       print(f"保存密钥错误 {filepath}: {str(e)}")
       if os.path.exists(temp_path):
           os.remove(temp_path)
       return False
def generate_keys():
   try:
       print("\n=== 开始生成密钥 ===")
       
       # 初始化配对群和 CP-ABE 方案
       group = PairingGroup('SS512')
       cpabe = CPabe_BSW07(group)
        # 生成公钥和主密钥
       pk, msk = cpabe.setup()
       print("生成基础密钥对完成")
        # 定义每个角色的属性集
       attributes = {
           'contributor': ['contributor'],
           'expert': ['contributor', 'expert'],
           'administrator': ['contributor', 'expert', 'administrator']
       }
        # 创建密钥目录
       os.makedirs('keys', exist_ok=True)
       
       # 保存公钥
       if not save_key(pk, 'keys/public.key', group):
           raise Exception("保存公钥失败")
           
       # 保存主密钥
       if not save_key(msk, 'keys/master.key', group):
           raise Exception("保存主密钥失败")
        # 为每个角色生成并保存私钥
       for role, attrs in attributes.items():
           print(f"\n生成 {role} 的私钥...")
           private_key = cpabe.keygen(pk, msk, attrs)
           if not save_key(private_key, f'keys/private_{role}.key', group):
               raise Exception(f"保存 {role} 的私钥失败")
       print("\nKeys have been generated and saved")
       print("\n生成的文件:")
       print("- keys/public.key")
       print("- keys/master.key")
       for role in attributes.keys():
           print(f"- keys/private_{role}.key")
           
       return True
       
   except Exception as e:
       print(f"\n密钥生成错误: {str(e)}")
       return False
if __name__ == '__main__':
   generate_keys()

