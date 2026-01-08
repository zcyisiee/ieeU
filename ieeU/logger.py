from datetime import datetime
from typing import Dict


class Logger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }
        self.errors = []
    
    def log_progress(
        self, 
        current: int, 
        total: int, 
        image_path: str, 
        success: bool
    ):
        self.stats['total'] += 1
        if success:
            self.stats['success'] += 1
            status = "✓"
        else:
            self.stats['failed'] += 1
            status = "✗"
        
        print(
            f"Processing {current}/{total}: {image_path} ... {status}"
        )
    
    def log_error(self, image_path: str, error: str):
        error_msg = f"Error for {image_path}: {error}"
        self.errors.append(error_msg)
        print(error_msg)
    
    def log_summary(self):
        self.stats['end_time'] = datetime.now()
        
        print("\n" + "=" * 50)
        print("Processing Summary")
        print("=" * 50)
        print(f"Total images: {self.stats['total']}")
        print(f"Success: {self.stats['success']}")
        print(f"Failed: {self.stats['failed']}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors[:10]:
                print(f"  - {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")
        
        print("=" * 50)
    
    def log_file_info(self, filename: str, image_count: int):
        print(f"\nProcessing: {filename}")
        print(f"Found {image_count} images...")
    
    def log_output(self, filename: str):
        print(f"Output: {filename}")
    
    def log_start(self):
        self.stats['start_time'] = datetime.now()
        print("ieeU - Image to Description Converter")
        print("=" * 50)
