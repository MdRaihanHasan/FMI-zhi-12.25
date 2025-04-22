# this is views.py. Created by Zhi 2024.12
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import fm
import os
import time
import json

views = Blueprint('views', __name__)


@views.route('/welcome')
@login_required
def welcome():
    try:
        files_info = []
        root_base = 'root'

        # 只获取并显示文件夹
        for folder_name in os.listdir(root_base):
            folder_path = os.path.join(root_base, folder_name)
            if os.path.isdir(folder_path):
                files_info.append({
                    'name': folder_name,
                    'is_dir': True,
                    'path': folder_name
                })

        # 按文件夹名称排序
        files_info.sort(key=lambda x: x['name'].lower())

        return render_template("welcome.html",
                               user=current_user,
                               files=files_info,
                               file_count=len(files_info),
                               current_path=None)
    except Exception as e:
        print(f"Error in welcome route: {e}")
        return render_template("welcome.html",
                               user=current_user,
                               files=[],
                               file_count=0,
                               current_path=None)


@views.route('/open_folder/<path:folder_name>')
@login_required
def open_folder(folder_name):
    try:
        print("\n=== Debug open_folder ===")
        print(f"Opening folder: {folder_name}")

        files_info = []
        folder_path = os.path.join('root', folder_name)

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            flash('Folder not found', 'error')
            return redirect(url_for('views.welcome'))

        # 读取文件夹的元数据
        metadata_path = f'metadata/{folder_name}.lst'  # 移除 .cpabe 后缀
        metadata_content = ""
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata_content = f.read()
                print(f"Metadata loaded from: {metadata_path}")
            except Exception as e:
                print(f"Error reading metadata: {e}")

        # 获取文件夹中的文件
        for filename in os.listdir(folder_path):
            if filename.endswith('.cpabe'):
                file_id = filename.replace('.cpabe', '')
                display_name = file_id

                # 从元数据中获取原始文件名
                if metadata_content:
                    for block in metadata_content.split('BLOCK\n=====\n')[1:]:
                        if file_id in block:
                            for line in block.split('\n'):
                                if line.startswith('Original File Name:'):
                                    display_name = line.split(': ')[1].strip()
                                    break

                file_path = os.path.join(folder_name, filename)
                print(f"Found file: {filename}, display as: {display_name}")

                files_info.append({
                    'name': display_name,
                    'is_dir': False,
                    'path': file_path,
                    'size': os.path.getsize(os.path.join(folder_path, filename))
                })

        files_info.sort(key=lambda x: x['name'].lower())
        return render_template('welcome.html',
                            user=current_user,
                            files=files_info,
                            file_count=len(files_info),
                            current_path=folder_name)

    except Exception as e:
        print(f"Error opening folder: {e}")
        import traceback
        print(traceback.format_exc())
        flash('Error opening folder', 'error')
        return redirect(url_for('views.welcome'))


@views.route('/fileSearch', methods=['GET', 'POST'])
@login_required
def fileSearch():
    results = []
    search_time = 0

    if request.method == 'POST':
        try:
            start_time = time.time()
            keywords = request.form.get('keywords', '').lower()
            folder = request.form.get('folder-select', 'ROOT')

            print("\n=== Search Debug Info ===")
            print(f"Keywords: {keywords}")
            print(f"Folder: {folder}")

            # 搜索指定文件夹中的所有加密文件
            folder_path = os.path.join('root', folder)
            if os.path.exists(folder_path):
                # 遍历文件夹中的所有 .cpabe 文件
                for filename in os.listdir(folder_path):
                    if filename.endswith('.cpabe'):
                        file_path = os.path.join(folder_path, filename)
                        print(f"Processing file: {file_path}")

                        try:
                            # 创建临时解密文件
                            temp_dir = 'temp_decrypted'
                            os.makedirs(temp_dir, exist_ok=True)
                            temp_decrypted_path = os.path.join(temp_dir, f'search_dec_{int(time.time())}_{filename}')

                            # 尝试解密文件
                            decrypted_path = fm.decrypt_file(file_path, current_user.attribute, temp_decrypted_path)
                            if decrypted_path:
                                # 读取解密后的内容
                                with open(decrypted_path, 'r') as f:
                                    content = f.read().lower()

                                # 检查关键词是否在内容中
                                if keywords in content:
                                    results.append({
                                        'name': filename,
                                        'path': os.path.join(folder, filename),
                                        'size': os.path.getsize(file_path),
                                        'matched': True
                                    })
                                    print(f"Found match in file: {filename}")

                                # 删除临时解密文件
                                os.remove(decrypted_path)

                        except Exception as e:
                            print(f"Error processing file {filename}: {str(e)}")
                            continue

            search_time = time.time() - start_time
            print(f"Search completed in {search_time:.4f} seconds")
            print(f"Found {len(results)} results")

        except Exception as e:
            print(f"Search error: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('Error during search', 'error')

    return render_template('fileSearch.html',
                           user=current_user,
                           results=results,
                           search_time=search_time)


@views.route('/readFile', methods=['GET'])
@login_required
def readFile():
    try:
        file_metadata = request.args.get('metadata')
        if not file_metadata:
            flash('No file metadata provided.', 'error')
            return redirect(url_for('views.welcome'))

        metadata = json.loads(file_metadata)
        file_path = metadata.get('Storage Path')

        if not file_path or not os.path.exists(file_path):
            flash('File not found.', 'error')
            return redirect(url_for('views.welcome'))

        # 使用新的解密方法
        decrypted_path = fm.decrypt_file(file_path, current_user.attribute)
        if not decrypted_path:
            flash('Unable to decrypt file. Access denied.', 'error')
            return redirect(url_for('views.welcome'))

        try:
            return send_file(
                decrypted_path,
                as_attachment=True,
                download_name=metadata.get('Original File Name', 'downloaded_file')
            )
        finally:
            # 清理解密后的临时文件
            if os.path.exists(decrypted_path):
                os.remove(decrypted_path)

    except Exception as e:
        flash(f'Error reading file: {str(e)}', 'error')
        return redirect(url_for('views.welcome'))


@views.route('/fileNameEncryption', methods=['GET', 'POST'])
@login_required
def fileNameEncryption():
    if request.method == 'POST':
        try:
            print("\n=== Debug File Upload ===")
            encryption_attribute = request.form.get('encryption-attribute', '').strip()
            folder_name = request.form.get('folder-name', '').strip()
            file = request.files.get('file-upload')
            keywords = request.form.get('file-name', '').strip()

            if not all([file, folder_name, encryption_attribute, keywords]):
                raise ValueError("Missing required fields")

            if file.filename == '':
                raise ValueError("No selected file")

            # 使用新的加密方法
            result = fm.secure_and_save_file(file, folder_name, encryption_attribute)
            if not result:
                raise ValueError("File encryption failed")

            original_filename, random_file_name, file_path = result

            # 创建元数据块
            block_content = (
                f"Original File Name: {original_filename}\n"
                f"Encrypted File Name: {random_file_name}\n"
                f"Attribute: {encryption_attribute}\n"
                f"Keywords: {keywords}\n"
                f"Owner: {current_user.username}\n"
                f"Storage Path: {file_path}\n"
                f"Upload Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            # 更新元数据
            folder_metadata_path = fm.get_metadata_path(folder_name)
            if fm.update_metadata_file(folder_metadata_path, encryption_attribute, block_content):
                flash('File encrypted and uploaded successfully.', 'success')
            else:
                flash('File uploaded but metadata update failed.', 'warning')

            return redirect(url_for('views.fileNameEncryption'))

        except Exception as e:
            print(f"Upload Error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('views.fileNameEncryption'))

    return render_template("fileNameEncryption.html", user=current_user)


@views.route('/createFolder', methods=['GET', 'POST'])
@login_required
def createFolder():
    if request.method == 'POST':
        try:
            # 获取表单数据
            encryption_attribute = request.form.get('encryption-attribute')
            folder_name = request.form.get('folder-name')

            print("=== Create Folder Debug Info ===")
            print(f"Folder name: {folder_name}")
            print(f"Encryption attribute: {encryption_attribute}")

            if not folder_name:
                flash('Please input folder name', 'error')
                return redirect(request.url)

            # 构建文件夹路径
            folder_path = os.path.join('root', folder_name)
            print(f"Creating folder at: {folder_path}")

            # 检查文件夹是否已存在
            if os.path.exists(folder_path):
                flash('Folder already exists', 'error')
                return redirect(request.url)

            try:
                # 创建文件夹
                os.makedirs(folder_path)
                print(f"Folder created successfully at {folder_path}")

                # 创建元数据文件
                metadata_content = (
                    f"HEADER: {encryption_attribute} (0, 2)\n"
                    f"BLOCK\n"
                    f"=====\n"
                    f"Folder Name: {folder_name}\n"
                    f"Creation Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Creator: {current_user.username}\n"
                    f"Attribute: {encryption_attribute}\n"
                )

                metadata_path = os.path.join('metadata', f'{folder_name}.lst.cpabe')
                print(f"Creating metadata file at: {metadata_path}")

                # 确保metadata目录存在
                os.makedirs('metadata', exist_ok=True)

                # 写入元数据
                with open(metadata_path, 'w') as f:
                    f.write(metadata_content)

                print("Metadata file created successfully")
                flash('Folder created successfully', 'success')
                return redirect(url_for('views.welcome'))

            except Exception as e:
                print(f"Error creating folder: {str(e)}")
                if os.path.exists(folder_path):
                    os.rmdir(folder_path)
                flash('Error creating folder', 'error')
                return redirect(request.url)

        except Exception as e:
            print(f"Error in createFolder: {str(e)}")
            import traceback
            traceback.print_exc()
            flash('Error processing request', 'error')
            return redirect(request.url)

    return render_template('createFolder.html', user=current_user)


@views.route('/viewFile/<path:filename>')
@login_required
def viewFile(filename):
    try:
        print("\n=== Starting viewFile function ===")
        # 使用绝对路径
        root_dir = os.path.abspath('root')
        temp_dir = os.path.abspath('temp_decrypted')

        # 构建完整的文件路径
        file_path = os.path.join(root_dir, filename)
        print(f"Original file path: {file_path}")

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            flash('File not found.', 'error')
            return redirect(url_for('views.welcome'))

        # 确保临时目录存在
        os.makedirs(temp_dir, exist_ok=True)

        # 创建唯一的临时文件名
        temp_filename = f'dec_{int(time.time())}_{os.path.basename(filename)}'
        temp_decrypted_path = os.path.join(temp_dir, temp_filename)
        print(f"Temp decrypted path: {temp_decrypted_path}")

        try:
            # 解密文件到临时位置
            decrypted_path = fm.decrypt_file(
                encrypted_path=file_path,
                role=current_user.attribute,
                output_path=temp_decrypted_path
            )

            if not decrypted_path:
                print("Decryption failed")
                flash('Unable to decrypt file.', 'error')
                return redirect(url_for('views.welcome'))

            print(f"File decrypted to: {decrypted_path}")

            # 读取解密后的文件内容
            with open(decrypted_path, 'r') as f:
                content = f.read()
            print("File content read successfully")

            # 确保原始文件仍然存在
            if not os.path.exists(file_path):
                print("Warning: Original file was removed!")

            return render_template('viewFile.html',
                                   filename=os.path.basename(filename),
                                   content=content,
                                   user=current_user)

        finally:
            # 只删除临时解密文件
            if os.path.exists(temp_decrypted_path):
                try:
                    os.remove(temp_decrypted_path)
                    print(f"Cleaned up temp file: {temp_decrypted_path}")
                except Exception as e:
                    print(f"Error cleaning up temp file: {e}")

    except Exception as e:
        print(f"Error in viewFile: {str(e)}")
        import traceback
        print(traceback.format_exc())
        flash('Error viewing file.', 'error')
        return redirect(url_for('views.welcome'))