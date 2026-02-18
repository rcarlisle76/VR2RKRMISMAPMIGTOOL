"""
Settings dialog for configuring mapping thresholds and AI settings.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QDoubleSpinBox, QCheckBox,
    QPushButton, QDialogButtonBox, QGroupBox, QComboBox,
    QPlainTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase


class SettingsDialog(QDialog):
    """Settings dialog for configuring mapping thresholds and AI settings."""

    def __init__(self, config_manager, parent=None):
        """
        Initialize the settings dialog.

        Args:
            config_manager: ConfigManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = config_manager.config
        self.init_ui()
        self.load_current_values()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(650)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Application Settings")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Tabs for organization
        tabs = QTabWidget()
        tabs.addTab(self._create_mapping_tab(), "Mapping")
        tabs.addTab(self._create_ai_tab(), "AI Settings")
        tabs.addTab(self._create_prompt_tab(), "LLM Prompt")
        layout.addWidget(tabs)

        layout.addStretch()

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok |
            QDialogButtonBox.Cancel |
            QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_changes)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _create_mapping_tab(self) -> QWidget:
        """Create mapping settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Fuzzy threshold
        fuzzy_group = QGroupBox("Fuzzy Matching Threshold")
        fuzzy_layout = QVBoxLayout()

        fuzzy_label = QLabel(
            "Minimum confidence score for fuzzy string matching (0.0-1.0).\n"
            "Higher values require more exact matches."
        )
        fuzzy_label.setWordWrap(True)
        fuzzy_label.setStyleSheet("color: #666; font-size: 10px;")
        fuzzy_layout.addWidget(fuzzy_label)

        self.fuzzy_spin = QDoubleSpinBox()
        self.fuzzy_spin.setMinimum(0.0)
        self.fuzzy_spin.setMaximum(1.0)
        self.fuzzy_spin.setSingleStep(0.05)
        self.fuzzy_spin.setDecimals(2)
        self.fuzzy_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QDoubleSpinBox:hover {
                border-color: #0176d3;
            }
        """)
        fuzzy_layout.addWidget(self.fuzzy_spin)

        fuzzy_group.setLayout(fuzzy_layout)
        layout.addWidget(fuzzy_group)

        # AI threshold
        ai_threshold_group = QGroupBox("AI Mapping Threshold")
        ai_threshold_layout = QVBoxLayout()

        ai_threshold_label = QLabel(
            "Minimum confidence score for AI-based mapping suggestions.\n"
            "Only mappings above this threshold will be suggested."
        )
        ai_threshold_label.setWordWrap(True)
        ai_threshold_label.setStyleSheet("color: #666; font-size: 10px;")
        ai_threshold_layout.addWidget(ai_threshold_label)

        self.ai_threshold_spin = QDoubleSpinBox()
        self.ai_threshold_spin.setMinimum(0.0)
        self.ai_threshold_spin.setMaximum(1.0)
        self.ai_threshold_spin.setSingleStep(0.05)
        self.ai_threshold_spin.setDecimals(2)
        self.ai_threshold_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QDoubleSpinBox:hover {
                border-color: #0176d3;
            }
        """)
        ai_threshold_layout.addWidget(self.ai_threshold_spin)

        ai_threshold_group.setLayout(ai_threshold_layout)
        layout.addWidget(ai_threshold_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_ai_tab(self) -> QWidget:
        """Create AI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Semantic matching checkbox
        self.semantic_check = QCheckBox("Enable Semantic Matching (Phase 1)")
        self.semantic_check.setStyleSheet("font-weight: bold;")
        semantic_hint = QLabel(
            "Uses local AI embeddings for intelligent field matching.\n"
            "No API key required. ~500MB model download on first use."
        )
        semantic_hint.setWordWrap(True)
        semantic_hint.setStyleSheet("color: #666; font-size: 9px; margin-left: 24px;")
        layout.addWidget(self.semantic_check)
        layout.addWidget(semantic_hint)

        layout.addSpacing(10)

        # LLM matching checkbox
        self.llm_check = QCheckBox("Enable LLM-Based Mapping (Phase 2)")
        self.llm_check.setStyleSheet("font-weight: bold;")
        llm_hint = QLabel(
            "Uses Claude or OpenAI API for context-aware mapping.\n"
            "Requires valid API key. ~$0.003 per mapping operation."
        )
        llm_hint.setWordWrap(True)
        llm_hint.setStyleSheet("color: #666; font-size: 9px; margin-left: 24px;")
        layout.addWidget(self.llm_check)
        layout.addWidget(llm_hint)
        self.llm_check.stateChanged.connect(self._on_llm_enabled_changed)

        layout.addSpacing(10)

        # LLM Provider selection
        provider_group = QGroupBox("LLM Provider")
        provider_layout = QVBoxLayout()

        provider_label = QLabel("Select which LLM service to use:")
        provider_label.setStyleSheet("color: #666; font-size: 10px;")
        provider_layout.addWidget(provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("Claude (Anthropic)", "claude")
        self.provider_combo.addItem("OpenAI (GPT)", "openai")
        self.provider_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #0176d3;
            }
        """)
        provider_layout.addWidget(self.provider_combo)

        provider_group.setLayout(provider_layout)
        provider_group.setEnabled(False)
        self.provider_group = provider_group
        layout.addWidget(provider_group)

        # API Key input
        api_key_group = QGroupBox("API Key")
        api_key_layout = QVBoxLayout()

        api_key_label = QLabel(
            "Your API key for Claude or OpenAI (stored locally, never transmitted):"
        )
        api_key_label.setWordWrap(True)
        api_key_label.setStyleSheet("color: #666; font-size: 10px;")
        api_key_layout.addWidget(api_key_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-ant-... or sk-...")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #0176d3;
            }
        """)
        api_key_layout.addWidget(self.api_key_input)

        # Show/hide password button
        show_key_layout = QHBoxLayout()
        self.show_key_check = QCheckBox("Show API key")
        self.show_key_check.stateChanged.connect(self._on_show_key_changed)
        show_key_layout.addWidget(self.show_key_check)
        show_key_layout.addStretch()
        api_key_layout.addLayout(show_key_layout)

        api_key_group.setLayout(api_key_layout)
        api_key_group.setEnabled(False)
        self.api_key_group = api_key_group
        layout.addWidget(api_key_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_prompt_tab(self) -> QWidget:
        """Create LLM prompt editor tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Description
        desc_label = QLabel(
            "Customize the prompt sent to the LLM for field mapping.\n"
            "Leave empty to use the default prompt. Use {csv_columns} and {sf_fields} as placeholders."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(desc_label)

        # Prompt editor
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText(self._get_default_prompt())
        self.prompt_edit.setStyleSheet("""
            QPlainTextEdit {
                font-family: Consolas, Monaco, monospace;
                font-size: 10px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
            }
            QPlainTextEdit:hover {
                border-color: #0176d3;
            }
        """)
        layout.addWidget(self.prompt_edit)

        # Buttons row
        button_layout = QHBoxLayout()

        reset_button = QPushButton("Reset to Default")
        reset_button.clicked.connect(self._on_reset_prompt)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #706e6b;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5856;
            }
        """)
        button_layout.addWidget(reset_button)

        button_layout.addStretch()

        # Placeholder help
        help_label = QLabel("Placeholders: {csv_columns}, {sf_fields}, {object_label}")
        help_label.setStyleSheet("color: #666; font-size: 9px;")
        button_layout.addWidget(help_label)

        layout.addLayout(button_layout)

        widget.setLayout(layout)
        return widget

    def _get_default_prompt(self) -> str:
        """Return the default LLM prompt."""
        return """Map CSV columns to Salesforce fields.

CSV columns:
{csv_columns}

Salesforce {object_label} fields:
{sf_fields}

For each CSV column, find the best matching Salesforce field. Consider:
- Semantic meaning (email vs e-mail, phone vs telephone)
- Data types (date columns -> date fields)
- Common abbreviations (amt=amount, num=number, qty=quantity)
- Business context (BillingStreet vs ShippingStreet)

Respond with ONLY a JSON array, no other text. Format:
[
  {{"source": "csv_column_name", "target": "SalesforceField__c", "confidence": 0.95, "reasoning": "why this matches"}},
  {{"source": "another_column", "target": "AnotherField__c", "confidence": 0.85, "reasoning": "semantic similarity"}}
]

If no good matches, return: []"""

    def _on_reset_prompt(self):
        """Reset prompt to default."""
        self.prompt_edit.setPlainText("")

    def _on_llm_enabled_changed(self):
        """Handle LLM checkbox state change."""
        enabled = self.llm_check.isChecked()
        self.provider_group.setEnabled(enabled)
        self.api_key_group.setEnabled(enabled)

    def _on_show_key_changed(self):
        """Handle show/hide API key checkbox."""
        if self.show_key_check.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)

    def load_current_values(self):
        """Load current configuration values into UI."""
        self.fuzzy_spin.setValue(self.config.fuzzy_mapping_threshold)
        self.ai_threshold_spin.setValue(self.config.ai_mapping_threshold)
        self.semantic_check.setChecked(self.config.use_semantic_matching)
        self.llm_check.setChecked(self.config.use_llm_mapping)

        # Set provider combo by data value
        index = self.provider_combo.findData(self.config.llm_provider)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)

        self.api_key_input.setText(self.config.claude_api_key)
        self._on_llm_enabled_changed()

        # Load custom prompt (empty = use default, shown as placeholder)
        self.prompt_edit.setPlainText(self.config.llm_prompt)

    def apply_changes(self):
        """Apply settings changes without closing."""
        self.config_manager.update(
            fuzzy_mapping_threshold=self.fuzzy_spin.value(),
            ai_mapping_threshold=self.ai_threshold_spin.value(),
            use_semantic_matching=self.semantic_check.isChecked(),
            use_llm_mapping=self.llm_check.isChecked(),
            llm_provider=self.provider_combo.currentData(),
            claude_api_key=self.api_key_input.text(),
            llm_prompt=self.prompt_edit.toPlainText()
        )
        self.config_manager.save()

    def accept(self):
        """Handle OK button - apply and close."""
        self.apply_changes()
        super().accept()
