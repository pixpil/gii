from pyqode.core.api import FoldDetector, TextBlockHelper


class JSONFoldDetector(FoldDetector):
    """
    Fold detector specialised to parse JSON documents.
    """
    def detect_fold_level(self, prev_block, block):
        if prev_block:
            prev_text = prev_block.text().strip()
        else:
            prev_text = ''
        if '[]' not in prev_text and '{}' not in prev_text:
            if prev_text.endswith(('{', '[')):
                return TextBlockHelper.get_fold_lvl(prev_block) + 1
            if prev_text.replace(',', '').endswith(('}', ']')):
                return TextBlockHelper.get_fold_lvl(prev_block) - 1
        return TextBlockHelper.get_fold_lvl(prev_block)
