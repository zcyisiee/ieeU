import argparse
import os
import sys

from .config import Config
from .processor import Processor


def main():
    """Main entry point for ieeU CLI."""
    
    parser = argparse.ArgumentParser(
        prog="ieeU",
        description="将Markdown中的图片链接替换为VLM生成的描述性文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ieeU run                  # 执行图片描述转换
  ieeU run --verbose        # 详细输出模式
  ieeU --version            # 显示版本号
  
配置文件:
  ~/.ieeU/settings.json
        """
    )
    
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="1.1.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<命令>",
        description="可用的命令"
    )
    
    # run command
    run_parser = subparsers.add_parser(
        "run",
        help="执行图片描述转换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ieeU run
  ieeU run --verbose
        """
    )
    run_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出模式"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    if args.command == "run":
        verbose = getattr(args, "verbose", False)
        
        directory = os.path.abspath(".")
        
        if not os.path.isdir(directory):
            print(f"错误: 目录不存在: {directory}")
            sys.exit(1)
        
        config = Config.load()
        
        try:
            config.validate()
        except ValueError as e:
            print(f"配置错误: {e}")
            print(f"请创建 ~/.ieeU/settings.json，包含 endpoint、key 和 modelName")
            sys.exit(1)
        
        processor = Processor(config, verbose)
        processor.process_directory(directory)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
