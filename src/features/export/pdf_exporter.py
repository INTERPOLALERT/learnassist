"""
PDF Exporter Module
Exports essays to PDF format with academic formatting.

Features:
- Template-based formatting (APA, MLA, Chicago, Harvard)
- Academic styling (margins, fonts, spacing)
- Title page generation
- Headers and footers
- Page numbers
- Citation formatting

Author: Academic Command Center
Phase: 6 Sprint 1
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime
import os
import re

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        Table, TableStyle, Frame, PageTemplate
    )
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    if not TYPE_CHECKING:
        # Mock types when not available
        SimpleDocTemplate = Any
        Paragraph = Any
        ParagraphStyle = Any
        canvas = Any


class PDFExporter:
    """
    Exports essays to PDF format with academic templates.
    """

    def __init__(self):
        """Initialize PDF exporter."""
        if not PDF_AVAILABLE:
            raise ImportError(
                "reportlab not installed. Install with: pip install reportlab"
            )

    def export(
        self,
        essay_data: Dict[str, Any],
        output_path: str,
        template: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export essay to PDF format.

        Args:
            essay_data: Essay data including content, metadata
            output_path: Path to save PDF file
            template: Academic template (apa, mla, chicago, harvard, generic)
            options: Additional export options
                - include_title_page: bool (default True)
                - include_references: bool (default True)
                - page_numbers: bool (default True)
                - line_spacing: float (default 2.0)
                - font_name: str (default "Times-Roman")
                - font_size: int (default 12)

        Returns:
            Export result with file info
        """
        options = options or {}
        template = template or "generic"

        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Get template config
        config = self._get_template_config(template, options)

        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            topMargin=config["margin_top"] * inch,
            bottomMargin=config["margin_bottom"] * inch,
            leftMargin=config["margin_left"] * inch,
            rightMargin=config["margin_right"] * inch
        )

        # Build document content
        story = []

        # Add title page
        if options.get("include_title_page", True):
            title_page = self._build_title_page(essay_data, template, config)
            story.extend(title_page)
            story.append(PageBreak())

        # Add main content
        content_elements = self._build_content(essay_data, template, config)
        story.extend(content_elements)

        # Add references
        if options.get("include_references", True) and essay_data.get("sources"):
            story.append(PageBreak())
            refs = self._build_references(essay_data, template, config)
            story.extend(refs)

        # Build PDF with page numbers if requested
        if options.get("page_numbers", True):
            doc.build(
                story,
                onFirstPage=lambda c, d: self._add_page_number(c, d, template, config, first=True),
                onLaterPages=lambda c, d: self._add_page_number(c, d, template, config, first=False)
            )
        else:
            doc.build(story)

        # Get file size
        file_size = os.path.getsize(output_path)

        return {
            "success": True,
            "file_path": output_path,
            "file_size": file_size,
            "format": "pdf",
            "template": template
        }

    def _get_template_config(
        self,
        template: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get configuration for specific template."""

        # Base configuration
        base_config = {
            "font_name": options.get("font_name", "Times-Roman"),
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
                "running_head": True,
                "page_number_location": "top_right",
                "title_page_required": True,
            },
            "mla": {
                "header_format": "last_name_page",
                "page_number_location": "top_right",
                "title_page_required": False,
            },
            "chicago": {
                "title_page_required": True,
                "page_number_location": "bottom_center",
                "footnotes": True,
            },
            "harvard": {
                "title_page_required": True,
                "page_number_location": "bottom_center",
            },
            "generic": {
                "title_page_required": False,
            }
        }

        # Merge configurations
        config = {**base_config, **template_configs.get(template, {})}
        return config

    def _get_styles(self, config: Dict[str, Any]) -> Dict[str, ParagraphStyle]:
        """Create paragraph styles based on config."""

        styles = getSampleStyleSheet()

        # Normal style (body text)
        normal = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName=config["font_name"],
            fontSize=config["font_size"],
            leading=config["font_size"] * config["line_spacing"],
            alignment=TA_JUSTIFY,
            firstLineIndent=0.5 * inch
        )

        # Heading styles
        heading1 = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontName=config["font_name"],
            fontSize=config["font_size"],
            leading=config["font_size"] * 1.5,
            alignment=TA_CENTER,
            spaceAfter=12
        )

        heading2 = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontName=config["font_name"],
            fontSize=config["font_size"],
            leading=config["font_size"] * 1.5,
            alignment=TA_LEFT,
            spaceAfter=12
        )

        # Title page styles
        title = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontName=config["font_name"],
            fontSize=config["font_size"] + 4,
            alignment=TA_CENTER,
            spaceAfter=12
        )

        centered = ParagraphStyle(
            'Centered',
            parent=styles['Normal'],
            fontName=config["font_name"],
            fontSize=config["font_size"],
            alignment=TA_CENTER
        )

        # Reference style (hanging indent)
        reference = ParagraphStyle(
            'Reference',
            parent=styles['Normal'],
            fontName=config["font_name"],
            fontSize=config["font_size"],
            leading=config["font_size"] * 2.0,
            leftIndent=0.5 * inch,
            firstLineIndent=-0.5 * inch,
            alignment=TA_LEFT
        )

        return {
            'normal': normal,
            'heading1': heading1,
            'heading2': heading2,
            'title': title,
            'centered': centered,
            'reference': reference
        }

    def _build_title_page(
        self,
        essay_data: Dict[str, Any],
        template: str,
        config: Dict[str, Any]
    ) -> List[Any]:
        """Build title page elements based on template."""

        styles = self._get_styles(config)
        elements = []

        if template == "apa":
            return self._build_apa_title_page(essay_data, styles)
        elif template == "mla":
            return self._build_mla_header(essay_data, styles)
        elif template == "chicago":
            return self._build_chicago_title_page(essay_data, styles)
        elif template == "harvard":
            return self._build_harvard_title_page(essay_data, styles)
        else:
            return self._build_generic_title_page(essay_data, styles)

    def _build_apa_title_page(
        self,
        essay_data: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Build APA-style title page."""

        elements = []

        # Running head (top left)
        running_head = Paragraph(
            f"Running head: {essay_data.get('title', 'ESSAY')[:50].upper()}",
            styles['normal']
        )
        elements.append(running_head)

        # Spacer to center content
        elements.append(Spacer(1, 2.5 * inch))

        # Title (centered, bold)
        title = Paragraph(
            f"<b>{essay_data.get('title', 'Untitled Essay')}</b>",
            styles['title']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5 * inch))

        # Student name
        author = Paragraph(
            essay_data.get('author', 'Student Name'),
            styles['centered']
        )
        elements.append(author)
        elements.append(Spacer(1, 0.25 * inch))

        # Institution
        institution = Paragraph(
            essay_data.get('institution', 'University Name'),
            styles['centered']
        )
        elements.append(institution)

        # Course
        if essay_data.get('course_name'):
            elements.append(Spacer(1, 0.25 * inch))
            course = Paragraph(
                essay_data.get('course_name'),
                styles['centered']
            )
            elements.append(course)

        # Date
        elements.append(Spacer(1, 0.5 * inch))
        date = Paragraph(
            datetime.now().strftime("%B %d, %Y"),
            styles['centered']
        )
        elements.append(date)

        return elements

    def _build_mla_header(
        self,
        essay_data: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Build MLA-style header (no title page)."""

        elements = []

        # Student info (top left, double-spaced)
        elements.append(Paragraph(essay_data.get('author', 'Student Name'), styles['normal']))
        elements.append(Paragraph(essay_data.get('instructor', 'Instructor Name'), styles['normal']))
        elements.append(Paragraph(essay_data.get('course_name', 'Course Name'), styles['normal']))
        elements.append(Paragraph(datetime.now().strftime("%d %B %Y"), styles['normal']))

        elements.append(Spacer(1, 0.25 * inch))

        # Title (centered)
        title = Paragraph(
            essay_data.get('title', 'Untitled Essay'),
            styles['centered']
        )
        elements.append(title)

        elements.append(Spacer(1, 0.25 * inch))

        return elements

    def _build_chicago_title_page(
        self,
        essay_data: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Build Chicago-style title page."""

        elements = []

        # Spacer (1/3 down page)
        elements.append(Spacer(1, 3 * inch))

        # Title (centered)
        title = Paragraph(
            f"<b>{essay_data.get('title', 'Untitled Essay')}</b>",
            styles['title']
        )
        elements.append(title)

        # Spacer
        elements.append(Spacer(1, 3 * inch))

        # "By"
        elements.append(Paragraph("By", styles['centered']))
        elements.append(Spacer(1, 0.25 * inch))

        # Author
        elements.append(Paragraph(essay_data.get('author', 'Student Name'), styles['centered']))
        elements.append(Spacer(1, 0.5 * inch))

        # Course and institution
        if essay_data.get('course_name'):
            elements.append(Paragraph(essay_data.get('course_name'), styles['centered']))
            elements.append(Spacer(1, 0.25 * inch))

        elements.append(Paragraph(essay_data.get('institution', 'University Name'), styles['centered']))
        elements.append(Spacer(1, 0.25 * inch))

        # Date
        elements.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles['centered']))

        return elements

    def _build_harvard_title_page(
        self,
        essay_data: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Build Harvard-style title page."""
        # Similar to generic
        return self._build_generic_title_page(essay_data, styles)

    def _build_generic_title_page(
        self,
        essay_data: Dict[str, Any],
        styles: Dict[str, ParagraphStyle]
    ) -> List[Any]:
        """Build generic title page."""

        elements = []

        # Spacer
        elements.append(Spacer(1, 2.5 * inch))

        # Title
        title = Paragraph(
            f"<b><font size=16>{essay_data.get('title', 'Untitled Essay')}</font></b>",
            styles['centered']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5 * inch))

        # Author
        elements.append(Paragraph(essay_data.get('author', 'Student Name'), styles['centered']))
        elements.append(Spacer(1, 0.25 * inch))

        # Course
        if essay_data.get('course_name'):
            elements.append(Paragraph(essay_data.get('course_name'), styles['centered']))
            elements.append(Spacer(1, 0.25 * inch))

        # Date
        elements.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles['centered']))

        return elements

    def _build_content(
        self,
        essay_data: Dict[str, Any],
        template: str,
        config: Dict[str, Any]
    ) -> List[Any]:
        """Build main content elements."""

        styles = self._get_styles(config)
        elements = []

        content = essay_data.get('content', '')

        if not content:
            elements.append(Paragraph("(No content available)", styles['normal']))
            return elements

        # Split content into paragraphs
        paragraphs = content.split("\n\n")

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            # Check if heading
            if para_text.startswith("#"):
                level = para_text.count("#", 0, 3)
                text = para_text.lstrip("#").strip()

                if level == 1:
                    elements.append(Paragraph(f"<b>{text}</b>", styles['heading1']))
                elif level == 2:
                    elements.append(Paragraph(f"<b>{text}</b>", styles['heading2']))
                else:
                    elements.append(Paragraph(f"<b>{text}</b>", styles['heading2']))
            else:
                # Regular paragraph
                elements.append(Paragraph(para_text, styles['normal']))

        return elements

    def _build_references(
        self,
        essay_data: Dict[str, Any],
        template: str,
        config: Dict[str, Any]
    ) -> List[Any]:
        """Build references section."""

        styles = self._get_styles(config)
        elements = []

        # Heading
        if template == "apa":
            heading_text = "References"
        elif template == "mla":
            heading_text = "Works Cited"
        elif template == "chicago":
            heading_text = "Bibliography"
        else:
            heading_text = "References"

        elements.append(Paragraph(f"<b>{heading_text}</b>", styles['heading1']))
        elements.append(Spacer(1, 0.25 * inch))

        # Add sources
        sources = essay_data.get('sources', [])

        for source in sources:
            citation = self._format_citation(source, template)
            elements.append(Paragraph(citation, styles['reference']))

        return elements

    def _format_citation(
        self,
        source: Dict[str, Any],
        template: str
    ) -> str:
        """Format citation according to template style."""

        # Check for pre-formatted citation
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
            return f'{author}. "{title}." {year}.'
        elif template == "harvard":
            return f"{author} ({year}) {title}."
        else:
            return f"{author} ({year}). {title}."

    def _add_page_number(
        self,
        canvas_obj: Any,
        doc: Any,
        template: str,
        config: Dict[str, Any],
        first: bool = False
    ) -> None:
        """Add page number to page."""

        page_num = canvas_obj.getPageNumber()

        # APA: Skip page number on first page, top right on others
        if template == "apa":
            if not first:
                canvas_obj.setFont(config["font_name"], config["font_size"])
                canvas_obj.drawRightString(
                    7.5 * inch,
                    10.5 * inch,
                    str(page_num)
                )

        # MLA: Top right with last name
        elif template == "mla":
            canvas_obj.setFont(config["font_name"], config["font_size"])
            # Would need last name from essay_data - simplified for now
            canvas_obj.drawRightString(
                7.5 * inch,
                10.5 * inch,
                str(page_num)
            )

        # Chicago/Harvard: Bottom center
        elif template in ["chicago", "harvard"]:
            canvas_obj.setFont(config["font_name"], config["font_size"])
            canvas_obj.drawCentredString(
                4.25 * inch,
                0.5 * inch,
                str(page_num)
            )

        # Generic: Bottom right
        else:
            canvas_obj.setFont(config["font_name"], config["font_size"])
            canvas_obj.drawRightString(
                7.5 * inch,
                0.5 * inch,
                str(page_num)
            )


def create_exporter() -> PDFExporter:
    """
    Factory function to create PDF exporter.

    Returns:
        PDFExporter instance

    Raises:
        ImportError: If reportlab not installed
    """
    if not PDF_AVAILABLE:
        raise ImportError(
            "reportlab library required for PDF export. "
            "Install with: pip install reportlab"
        )

    return PDFExporter()
