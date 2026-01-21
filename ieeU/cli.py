import argparse
import os
import sys

from .config import Config
from .processor import Processor


def main():
    """Main entry point for ieeU CLI."""
    
    parser = argparse.ArgumentParser(
        prog="ieeU",
        description="将PDF文件解析并将图片替换为VLM生成的描述性文本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ieeU process paper.pdf           # 处理PDF文件
  ieeU process paper.pdf -o ./out  # 指定输出目录
  ieeU run                         # 处理当前目录的full.md (向后兼容)
  ieeU --version                   # 显示版本号
  
配置文件:
  ~/.ieeU/settings.json
        """
    )
    
    parser.add_argument(
        "--version", "-V",
        action="version",
        version="1.2.1"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<命令>",
        description="可用的命令"
    )
    
    # process command (new main command)
    process_parser = subparsers.add_parser(
        "process",
        help="处理PDF文件：解析并替换图片为描述",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  ieeU process paper.pdf
  ieeU process paper.pdf -o ./output
  ieeU process paper.pdf --verbose
        """
    )
    process_parser.add_argument(
        "pdf_path",
        help="PDF文件路径"
    )
    process_parser.add_argument(
        "--output", "-o",
        help="输出目录（默认为PDF所在目录）",
        default=None
    )
    process_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出模式"
    )
    
    # run command (backward compatibility)
    run_parser = subparsers.add_parser(
        "run",
        help="处理当前目录的full.md文件（向后兼容）",
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
    
    config = Config.load()
    
    if args.command == "process":
        pdf_path = os.path.abspath(args.pdf_path)
        
        if not os.path.isfile(pdf_path):
            print(f"错误: PDF文件不存在: {pdf_path}")
            sys.exit(1)
        
        if not pdf_path.lower().endswith('.pdf'):
            print(f"错误: 文件不是PDF格式: {pdf_path}")
            sys.exit(1)
        
        if not config.mineru_token:
            print("错误: 未配置 mineruToken")
            print("请在 ~/.ieeU/settings.json 中添加 mineruToken")
            sys.exit(1)
        
        try:
            config.validate()
        except ValueError as e:
            print(f"配置错误: {e}")
            print("请确保 ~/.ieeU/settings.json 包含 endpoint、key、modelName 和 mineruToken")
            sys.exit(1)
        
        output_dir = args.output
        if output_dir:
            output_dir = os.path.abspath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = os.path.dirname(pdf_path)
        
        verbose = getattr(args, "verbose", False)
        processor = Processor(config, verbose)
        processor.process_pdf(pdf_path, output_dir)
    
    elif args.command == "run":
        verbose = getattr(args, "verbose", False)
        
        directory = os.path.abspath(".")
        
        if not os.path.isdir(directory):
            print(f"错误: 目录不存在: {directory}")
            sys.exit(1)
        
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
