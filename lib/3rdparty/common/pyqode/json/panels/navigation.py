import re
from pyqode.core.api import Panel, TextHelper, TextBlockHelper, FoldScope
from qtpy import QtCore, QtWidgets, QtGui


class NavigationPanel(Panel):
    """
    This panel show the position of the cursor in the document by showing
    the various parent nodes as toggle-able buttons.
    """
    def __init__(self):
        super(NavigationPanel, self).__init__()
        self._layout = QtWidgets.QHBoxLayout()
        self._layout.setContentsMargins(3, 3, 3, 3)
        self.setLayout(self._layout)
        self._widgets = []
        self._lock = False
        self._toggled = None

    def sizeHint(self):
        return QtCore.QSize(16, 32)

    def on_state_changed(self, state):
        if state:
            self.editor.cursorPositionChanged.connect(
                self._on_cursor_pos_changed)
        else:
            self.editor.cursorPositionChanged.disconnect(
                self._on_cursor_pos_changed)

    @staticmethod
    def extract_node_name(block):
        """
        Extracts the name of the node at ``block``
        :param block: QTextBlock to parse
        :return: name (str)
        """
        text = block.text().strip()
        node_name = re.search('"[^"\n]*("|\n):', text)
        if node_name:
            s, e = node_name.span()
            node_name = text[s: e].replace('"', '').replace(':', '')
        return node_name

    @staticmethod
    def get_parent_scopes(block):
        """
        Gets the list of hierarchical parent scopes of the current block.

        :param block: current block
        :return: list of QTextBlock
        """
        scopes = [block]
        scope = FoldScope.find_parent_scope(block)
        while scope is not None:
            ref = TextBlockHelper.get_fold_lvl(scopes[-1])
            if TextBlockHelper.get_fold_lvl(scope) < ref:
                # ignore sibling scopes
                scopes.append(scope)
            if scope.blockNumber() == 0:
                # stop
                scope = None
            else:
                # next parent
                scope = FoldScope.find_parent_scope(scope.previous())
        return reversed(scopes)

    def _clear_widgets(self):
        for w in self._widgets:
            try:
                self._layout.removeWidget(w)
                w.deleteLater()
            except TypeError:
                self._layout.removeItem(w)
        self._widgets[:] = []

    def _add_scope_widgets(self, scopes):
        for scope in scopes:
            name = self.extract_node_name(scope)
            if name is not None:
                w = QtWidgets.QToolButton(self)
                w.setText(name)
                w.scope = scope
                w.setCheckable(True)
                w.toggled.connect(self._on_bt_toggled)
                self._widgets.append(w)
                self._layout.addWidget(w)
        # toggle current and add a spacer
        if self._widgets:
            self._lock = True
            self._widgets[-1].setChecked(True)
            self._lock = False
            self._toggled = self._widgets[-1]
            s = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding)
            self._widgets.append(s)
            self._layout.addSpacerItem(s)

    def _on_cursor_pos_changed(self):
        if self._lock:
            return
        self._clear_widgets()
        scopes = self.get_parent_scopes(self.editor.textCursor().block())
        self._add_scope_widgets(scopes)

    def _on_bt_toggled(self, *ar):
        if not self._lock:
            self._lock = True
            for w in self._widgets:
                if w == self.sender():
                    break
            if self._toggled:
                self._toggled.setChecked(False)
            self._toggled = w
            th = TextHelper(self.editor)
            line = w.scope.blockNumber()
            th.goto_line(line, column=th.line_indent(line))
            self._lock = False
            self.editor.setFocus()
