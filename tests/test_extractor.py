import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ieeU.extractor import ImageExtractor, ImageReference


class TestImageExtractor:
    
    def test_extract_single_image(self):
        content = """
# Title

Some text here.

![](images/figure1.jpg)

More text.
"""
        references = ImageExtractor.extract_image_references(content)
        
        assert len(references) == 1
        assert references[0].path == "images/figure1.jpg"
        assert references[0].figure_num == 1
    
    def test_extract_multiple_images(self):
        content = """
# Title

![](images/fig1.jpg)

Some text.

![](images/fig2.jpg)

More text.

![](images/fig3.jpg)
"""
        references = ImageExtractor.extract_image_references(content)
        
        assert len(references) == 3
        assert references[0].path == "images/fig1.jpg"
        assert references[0].figure_num == 1
        assert references[1].path == "images/fig2.jpg"
        assert references[1].figure_num == 2
        assert references[2].path == "images/fig3.jpg"
        assert references[2].figure_num == 3
    
    def test_extract_no_images(self):
        content = """
# Title

Just some text without images.
"""
        references = ImageExtractor.extract_image_references(content)
        
        assert len(references) == 0
    
    def test_extract_with_alternative_text(self):
        content = """
![Alt text](images/figure.jpg)
"""
        references = ImageExtractor.extract_image_references(content)
        
        assert len(references) == 1
        assert references[0].path == "images/figure.jpg"
    
    def test_replace_single_image(self):
        content = "![](images/test.jpg)"
        replacements = {
            "![](images/test.jpg)": "```figure 1\nDescription\n```"
        }
        result = ImageExtractor.replace_images(content, replacements)
        
        assert result == "```figure 1\nDescription\n```"
    
    def test_replace_multiple_images(self):
        content = """
![](img1.jpg)

![](img2.jpg)
""".strip()
        replacements = {
            "![](img1.jpg)": "```figure 1\nDesc1\n```",
            "![](img2.jpg)": "```figure 2\nDesc2\n```"
        }
        result = ImageExtractor.replace_images(content, replacements)
        
        expected = """
```figure 1
Desc1
```

```figure 2
Desc2
```
""".strip()
        assert result == expected
    
    def test_get_image_paths_from_references(self):
        references = [
            ImageReference("images/fig1.jpg", 1, 1),
            ImageReference("images/fig2.jpg", 5, 2),
        ]
        
        base_dir = "/test/dir"
        paths = ImageExtractor.get_image_paths_from_references(
            references, 
            base_dir
        )
        
        assert paths["images/fig1.jpg"] == "/test/dir/images/fig1.jpg"
        assert paths["images/fig2.jpg"] == "/test/dir/images/fig2.jpg"
    
    def test_get_image_paths_filters_non_images_folder(self):
        references = [
            ImageReference("../other/path.jpg", 1, 1),
            ImageReference("images/fig1.jpg", 2, 2),
        ]
        
        base_dir = "/test/dir"
        paths = ImageExtractor.get_image_paths_from_references(
            references, 
            base_dir
        )
        
        assert len(paths) == 1
        assert "images/fig1.jpg" in paths


class TestImageReference:
    
    def test_repr(self):
        ref = ImageReference("test.jpg", 10, 1)
        repr_str = repr(ref)
        
        assert "test.jpg" in repr_str
        assert "10" in repr_str
        assert "1" in repr_str
