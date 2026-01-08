import os
import sys
from .config import Config
from .processor import Processor


def main():
    if len(sys.argv) < 2 or sys.argv[1] != 'run':
        print("Usage: ieeU run")
        sys.exit(1)
    
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    
    directory = sys.argv[2] if len(sys.argv) > 2 else "."
    
    directory = os.path.abspath(directory)
    
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: {directory}")
        sys.exit(1)
    
    config = Config.load()
    
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print(
            f"Please create ~/.ieeU/settings.json with "
            f"endpoint, key, and modelName."
        )
        sys.exit(1)
    
    processor = Processor(config, verbose)
    processor.process_directory(directory)


if __name__ == "__main__":
    main()
