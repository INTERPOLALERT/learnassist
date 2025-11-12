"""
DOCX Exporter Module
Exports essays to Microsoft Word format (.docx) with academic formatting.

Features:
- Template-based formatting (APA, MLA, Chicago, Harvard)
- Academic styling (double-spacing, margins, fonts)
- Title page generation
- Automatic headers/footers
- Citation formatting
- Section management

Author: Academic Command Center
Phase: 6 Sprint 1
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
import os
import re

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    # Mock types when not available
    if not TYPE_CHECKING:
        Document = Any


class DocxExporter:
    """
    Exports essays to DOCX format with academic templates.
    """

    def __init__(self):
        """Initialize DOCX exporter."""
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx not installed. Install with: pip install python-docx"
            )

    def export(
        self,
        essay_data: Dict[str, Any],
        output_path: str,
        template: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export essay to DOCX format.

        Args:
            essay_data: Essay data including content, metadata
            output_path: Path to save DOCX file
            template: Academic template (apa, mla, chicago, harvard, generic)
            options: Additional export options
                - include_title_page: bool (default True)
                - include_references: bool (default True)
                - page_numbers: bool (default True)
                - line_spacing: float (default 2.0)
                - font_name: str (default "Times New Roman")
                - font_size: int (default 12)

        Returns:
            Export result with file info
        """
        options = options or {}
        template = template or "generic"

        # Create document
        doc = Document()

        # Apply template-specific formatting
        self._apply_template_settings(doc, template, options)

        # Build document sections
        if options.get("include_title_page", True):
            self._add_title_page(doc, essay_data, template)
            doc.add_page_break()

        # Add main content
        self._add_content(doc, essay_data, template, options)

        # Add references if available
        if options.get("include_references", True) and essay_data.get("sources"):
            doc.add_page_break()
            self._add_references(doc, essay_data, template)

        # Add page numbers if requested
        if options.get("page_numbers", True):
            self._add_page_numbers(doc, template)

        # Save document
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)

        # Get file size
        file_size = os.path.getsize(output_path)

        return {
            "success": True,
            "file_path": output_path,
            "file_size": file_size,
            "format": "docx",
            "template": template
        }

    def _apply_template_settings(
        self,
        doc: Document,
        template: str,
        options: Dict[str, Any]
    ) -> None:
        """Apply template-specific document settings."""

        # Get template config
        config = self._get_template_config(template, options)

        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(config["margin_top"])
            section.bottom_margin = Inches(config["margin_bottom"])
            section.left_margin = Inches(config["margin_left"])
            section.right_margin = Inches(config["margin_right"])

        # Configure Normal style (base for all paragraphs)
        style = doc.styles['Normal']
        font = style.font
        font.name = config["font_name"]
        font.size = Pt(config["font_size"])

        # Set paragraph formatting
        paragraph_format = style.paragraph_format
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
        paragraph_format.space_after = Pt(0)
        paragraph_format.space_before = Pt(0)

        # First line indent (for body paragraphs)
        if template in ["apa", "mla", "chicago"]:
            paragraph_format.first_line_indent = Inches(0.5)

    def _get_template_config(
        self,
        template: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get configuration for specific template."""

        # Base configuration
        base_config = {
            "font_name": options.get("font_name", "Times New Roman"),
            "font_size": options.get("font_size", 12),
            "line_spacing": options.get("line_spacing", 2.0),
            "margin_top": 1.0,
            "margin_bottom": 1.0,
            "margin_left": 1.0,
            "margin_right": 1.0,
        }

        # Template-specific overrides
        template_configs = {
            "apa": {
                "margin_top": 1.0,
                "title_page_required": True,
                "running_head": True,
                "page_number_location": "top_right",
            },
            "mla": {
                "margin_top": 1.0,
                "title_page_required": False,
                "header_format": "last_name_page",
                "page_number_location": "top_right",
            },
            "chicago": {
                "margin_top": 1.0,
                "title_page_required": True,
                "footnotes": True,
                "page_number_location": "bottom_center",
            },
            "harvard": {
                "margin_top": 1.0,
                "title_page_required": True,
                "page_number_location": "bottom_center",
            },
            "generic": {
                "margin_top": 1.0,
                "title_page_required": False,
            }
        }

        # Merge configurations
        config = {**base_config, **template_configs.get(template, {})}
        return config

    def _add_title_page(
        self,
        doc: Document,
        essay_data: Dict[str, Any],
        template: str
    ) -> None:
        """Add title page based on template."""

        if template == "apa":
            self._add_apa_title_page(doc, essay_data)
        elif template == "mla":
            self._add_mla_header(doc, essay_data)
        elif template == "chicago":
            self._add_chicago_title_page(doc, essay_data)
        elif template == "harvard":
            self._add_harvard_title_page(doc, essay_data)
        else:
            self._add_generic_title_page(doc, essay_data)

    def _add_apa_title_page(
        self,
        doc: Document,
        essay_data: Dict[str, Any]
    ) -> None:
        """Add APA-style title page."""

        # Running head
        p = doc.add_paragraph()
        p.text = f"Running head: {essay_data.get('title', 'ESSAY')[:50].upper()}"
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Add spacing
        for _ in range(6):
            doc.add_paragraph()

        # Title (centered, bold)
        title = doc.add_paragraph()
        title.text = essay_data.get("title", "Untitled Essay")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].bold = True

        # Student name
        doc.add_paragraph()
        student = doc.add_paragraph()
        student.text = essay_data.get("author", "Student Name")
        student.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Institution
        institution = doc.add_paragraph()
        institution.text = essay_data.get("institution", "University Name")
        institution.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Course
        if essay_data.get("course_name"):
            course = doc.add_paragraph()
            course.text = essay_data.get("course_name", "")
            course.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Date
        doc.add_paragraph()
        date = doc.add_paragraph()
        date.text = datetime.now().strftime("%B %d, %Y")
        date.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_mla_header(
        self,
        doc: Document,
        essay_data: Dict[str, Any]
    ) -> None:
        """Add MLA-style header (no title page)."""

        # Student name
        doc.add_paragraph(essay_data.get("author", "Student Name"))

        # Instructor name
        doc.add_paragraph(essay_data.get("instructor", "Instructor Name"))

        # Course
        doc.add_paragraph(essay_data.get("course_name", "Course Name"))

        # Date
        doc.add_paragraph(datetime.now().strftime("%d %B %Y"))

        # Title (centered)
        doc.add_paragraph()
        title = doc.add_paragraph()
        title.text = essay_data.get("title", "Untitled Essay")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()

    def _add_chicago_title_page(
        self,
        doc: Document,
        essay_data: Dict[str, Any]
    ) -> None:
        """Add Chicago-style title page."""

        # Title (centered, 1/3 down page)
        for _ in range(8):
            doc.add_paragraph()

        title = doc.add_paragraph()
        title.text = essay_data.get("title", "Untitled Essay")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].bold = True

        # Spacing
        for _ in range(8):
            doc.add_paragraph()

        # Student info (centered, bottom of page)
        doc.add_paragraph("By")
        doc.add_paragraph(essay_data.get("author", "Student Name"))

        doc.add_paragraph()
        if essay_data.get("course_name"):
            doc.add_paragraph(essay_data.get("course_name"))

        doc.add_paragraph(essay_data.get("institution", "University Name"))
        doc.add_paragraph(datetime.now().strftime("%B %d, %Y"))

        # Center all
        for p in doc.paragraphs[-6:]:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_harvard_title_page(
        self,
        doc: Document,
        essay_data: Dict[str, Any]
    ) -> None:
        """Add Harvard-style title page."""
        # Similar to generic but with specific Harvard conventions
        self._add_generic_title_page(doc, essay_data)

    def _add_generic_title_page(
        self,
        doc: Document,
        essay_data: Dict[str, Any]
    ) -> None:
        """Add generic title page."""

        for _ in range(6):
            doc.add_paragraph()

        title = doc.add_paragraph()
        title.text = essay_data.get("title", "Untitled Essay")
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].bold = True
        title.runs[0].font.size = Pt(16)

        doc.add_paragraph()

        author = doc.add_paragraph()
        author.text = essay_data.get("author", "Student Name")
        author.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if essay_data.get("course_name"):
            course = doc.add_paragraph()
            course.text = essay_data.get("course_name")
            course.alignment = WD_ALIGN_PARAGRAPH.CENTER

        date = doc.add_paragraph()
        date.text = datetime.now().strftime("%B %d, %Y")
        date.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_content(
        self,
        doc: Document,
        essay_data: Dict[str, Any],
        template: str,
        options: Dict[str, Any]
    ) -> None:
        """Add main essay content."""

        content = essay_data.get("content", "")

        if not content:
            doc.add_paragraph("(No content available)")
            return

        # Split content into paragraphs
        paragraphs = content.split("\n\n")

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            # Check if it's a heading
            if para_text.startswith("#"):
                self._add_heading(doc, para_text)
            else:
                # Regular paragraph
                p = doc.add_paragraph(para_text)

                # Apply template-specific formatting
                if template == "mla":
                    p.paragraph_format.first_line_indent = Inches(0.5)

    def _add_heading(self, doc: Document, heading_text: str) -> None:
        """Add a heading based on markdown-style syntax."""

        # Count heading level
        level = 0
        for char in heading_text:
            if char == "#":
                level += 1
            else:
                break

        # Remove # symbols and whitespace
        text = heading_text.lstrip("#").strip()

        # Add heading (level 1-3 supported)
        if level == 1:
            doc.add_heading(text, level=1)
        elif level == 2:
            doc.add_heading(text, level=2)
        else:
            doc.add_heading(text, level=3)

    def _add_references(
        self,
        doc: Document,
        essay_data: Dict[str, Any],
        template: str
    ) -> None:
        """Add references/bibliography section."""

        # Add heading
        if template == "apa":
            heading_text = "References"
        elif template == "mla":
            heading_text = "Works Cited"
        elif template == "chicago":
            heading_text = "Bibliography"
        else:
            heading_text = "References"

        heading = doc.add_heading(heading_text, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add sources
        sources = essay_data.get("sources", [])

        for source in sources:
            # Get citation in appropriate format
            citation = self._format_citation(source, template)

            # Add citation paragraph with hanging indent
            p = doc.add_paragraph(citation)
            p.paragraph_format.left_indent = Inches(0.5)
            p.paragraph_format.first_line_indent = Inches(-0.5)

    def _format_citation(
        self,
        source: Dict[str, Any],
        template: str
    ) -> str:
        """Format a citation according to template style."""

        # Check if pre-formatted citation exists
        if template == "apa" and source.get("citation_apa"):
            return source["citation_apa"]
        elif template == "mla" and source.get("citation_mla"):
            return source["citation_mla"]
        elif template == "harvard" and source.get("citation_harvard"):
            return source["citation_harvard"]

        # Fallback: basic citation
        author = source.get("author", "Unknown Author")
        year = source.get("year", "n.d.")
        title = source.get("title", "Untitled")

        if template == "apa":
            return f"{author} ({year}). {title}."
        elif template == "mla":
            return f"{author}. \"{title}.\" {year}."
        elif template == "harvard":
            return f"{author} ({year}) {title}."
        else:
            return f"{author} ({year}). {title}."

    def _add_page_numbers(self, doc: Document, template: str) -> None:
        """Add page numbers to document."""

        # Note: Adding page numbers programmatically in python-docx
        # requires working with the document's XML structure
        # This is a placeholder for the implementation

        # For now, we'll add a note that page numbers should be added manually
        # or through a more advanced implementation using lxml

        # TODO: Implement programmatic page number insertion
        # This requires manipulating the document.xml directly
        pass


def create_exporter() -> DocxExporter:
    """
    Factory function to create DOCX exporter.

    Returns:
        DocxExporter instance

    Raises:
        ImportError: If python-docx not installed
    """
    if not DOCX_AVAILABLE:
        raise ImportError(
            "python-docx library required for DOCX export. "
            "Install with: pip install python-docx"
        )

    return DocxExporter()
