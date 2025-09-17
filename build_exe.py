import os
import subprocess
import sys

# 安装必要的依赖
def install_dependencies():
    print("正在安装必要的依赖...")
    try:
        # 安装pyinstaller用于打包
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        # 安装项目依赖
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装成功！")
    except Exception as e:
        print(f"依赖安装失败: {e}")
        sys.exit(1)

# 打包成exe文件
def build_exe():
    print("正在将Python脚本打包成exe文件...")
    try:
        # 构建PyInstaller命令
        cmd = [
            sys.executable,
            "-m", "PyInstaller",
            "--name", "我是扫码枪V3.1",  # 应用名称
            "--onefile",  # 打包成单个文件
            "--windowed",  # 不显示控制台窗口
            "--noconfirm",  # 覆盖已有文件，不询问
            "--icon", "barcode_icon.ico",  # 设置应用图标
            "keyboard_simulator.py"  # 要打包的主脚本
        ]

        # 执行打包命令
        subprocess.check_call(cmd)
        print("打包成功！")
        print("可执行文件位于 dist\我是扫码枪V3.1.exe")
    except Exception as e:
        print(f"打包失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_dependencies()
    build_exe()