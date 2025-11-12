"""
LaTeX Exporter Module
Exports essays to LaTeX format for compilation to PDF.

Features:
- Template-based LaTeX generation (APA, MLA, Chicago, Harvard)
- Academic document class setup
- Bibliography/BibTeX support
- Proper formatting and spacing
- Special character escaping
- Section management

Author: Academic Command Center
Phase: 6 Sprint 1
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import re


class LaTeXExporter:
    """
    Exports essays to LaTeX format with academic templates.
    """

    def __init__(self):
        """Initialize LaTeX exporter."""
        pass

    def export(
        self,
        essay_data: Dict[str, Any],
        output_path: str,
        template: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export essay to LaTeX format.

        Args:
            essay_data: Essay data including content, metadata
            output_path: Path to save .tex file
            template: Academic template (apa, mla, chicago, harvard, generic)
            options: Additional export options
                - include_title_page: bool (default True)
                - include_references: bool (default True)
                - compile_pdf: bool (default False)
                - line_spacing: float (default 2.0)

        Returns:
            Export result with file info
        """
        options = options or {}
        template = template or "generic"

        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Build LaTeX document
        latex_content = self._build_latex_document(essay_data, template, options)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        # Get file size
        file_size = os.path.getsize(output_path)

        # Optionally compile to PDF
        pdf_path = None
        if options.get("compile_pdf", False):
            pdf_path = self._compile_latex(output_path)

        return {
            "success": True,
            "file_path": output_path,
            "pdf_path": pdf_path,
            "file_size": file_size,
            "format": "latex",
            "template": template
        }

    def _build_latex_document(
        self,
        essay_data: Dict[str, Any],
        template: str,
        options: Dict[str, Any]
    ) -> str:
        """Build complete LaTeX document."""

        parts = []

        # Document class and preamble
        parts.append(self._build_preamble(essay_data, template, options))

        # Begin document
        parts.append("\n\\begin{document}\n")

        # Title page or header
        if options.get("include_title_page", True):
            parts.append(self._build_title_section(essay_data, template))

        # Main content
        parts.append(self._build_content(essay_data, template))

        # References
        if options.get("include_references", True) and essay_data.get("sources"):
            parts.append(self._build_references(essay_data, template))

        # End document
        parts.append("\n\\end{document}\n")

        return "\n".join(parts)

    def _build_preamble(
        self,
        essay_data: Dict[str, Any],
        template: str,
        options: Dict[str, Any]
    ) -> str:
        """Build LaTeX preamble with packages and settings."""

        preamble = []

        # Document class
        if template == "apa":
            preamble.append("\\documentclass[12pt,a4paper,apa]{article}")
        elif template == "mla":
            preamble.append("\\documentclass[12pt,letterpaper]{article}")
        elif template == "chicago":
            preamble.append("\\documentclass[12pt,letterpaper]{article}")
        else:
            preamble.append("\\documentclass[12pt,letterpaper]{article}")

        preamble.append("")

        # Packages
        preamble.append("% Packages")
        preamble.append("\\usepackage[utf8]{inputenc}")
        preamble.append("\\usepackage[english]{babel}")
        preamble.append("\\usepackage{times}  % Times New Roman font")

        # Margins
        if template == "apa":
            preamble.append("\\usepackage[margin=1in]{geometry}")
        elif template == "mla":
            preamble.append("\\usepackage[left=1in,right=1in,top=1in,bottom=1in]{geometry}")
        else:
            preamble.append("\\usepackage[margin=1in]{geometry}")

        # Line spacing
        line_spacing = options.get("line_spacing", 2.0)
        preamble.append("\\usepackage{setspace}")
        if line_spacing == 2.0:
            preamble.append("\\doublespacing")
        elif line_spacing == 1.5:
            preamble.append("\\onehalfspacing")
        else:
            preamble.append(f"\\setstretch{{{line_spacing}}}")

        # Additional packages
        preamble.append("\\usepackage{indentfirst}  % Indent first paragraph")
        preamble.append("\\usepackage{hyperref}  % Hyperlinks")
        preamble.append("\\usepackage{graphicx}  % Images")
        preamble.append("\\usepackage{cite}  % Citations")

        # Template-specific packages
        if template == "apa":
            preamble.append("\\usepackage{apacite}  % APA citations")
            preamble.append("\\usepackage{fancyhdr}  % Headers and footers")
            preamble.append("\\pagestyle{fancy}")
            preamble.append("\\fancyhf{}")
            preamble.append(f"\\rhead{{\\textit{{{essay_data.get('title', 'Essay')[:40]}}}}}")
            preamble.append("\\rfoot{\\thepage}")
        elif template == "mla":
            preamble.append("\\usepackage{fancyhdr}  % Headers")
            preamble.append("\\pagestyle{fancy}")
            preamble.append("\\fancyhf{}")
            author_last = essay_data.get('author', 'Student').split()[-1]
            preamble.append(f"\\rhead{{{author_last} \\thepage}}")
            preamble.append("\\renewcommand{\\headrulewidth}{0pt}")

        preamble.append("")

        # Metadata
        preamble.append("% Document metadata")
        title = self._escape_latex(essay_data.get('title', 'Untitled Essay'))
        author = self._escape_latex(essay_data.get('author', 'Student Name'))
        preamble.append(f"\\title{{{title}}}")
        preamble.append(f"\\author{{{author}}}")
        preamble.append(f"\\date{{\\today}}")

        preamble.append("")

        return "\n".join(preamble)

    def _build_title_section(
        self,
        essay_data: Dict[str, Any],
        template: str
    ) -> str:
        """Build title page or header section."""

        if template == "apa":
            return self._build_apa_title_page(essay_data)
        elif template == "mla":
            return self._build_mla_header(essay_data)
        elif template == "chicago":
            return self._build_chicago_title_page(essay_data)
        elif template == "harvard":
            return self._build_harvard_title_page(essay_data)
        else:
            return self._build_generic_title_page(essay_data)

    def _build_apa_title_page(self, essay_data: Dict[str, Any]) -> str:
        """Build APA title page."""

        lines = []

        # Running head
        running_head = essay_data.get('title', 'ESSAY')[:50].upper()
        lines.append(f"\\noindent Running head: {self._escape_latex(running_head)}")
        lines.append("\\vspace*{\\fill}")

        # Title (centered)
        title = self._escape_latex(essay_data.get('title', 'Untitled Essay'))
        lines.append(f"\\begin{{center}}")
        lines.append(f"\\textbf{{{title}}}")
        lines.append("\\\\[1cm]")

        # Author
        author = self._escape_latex(essay_data.get('author', 'Student Name'))
        lines.append(author)
        lines.append("\\\\[0.5cm]")

        # Institution
        institution = self._escape_latex(essay_data.get('institution', 'University Name'))
        lines.append(institution)

        # Course (if present)
        if essay_data.get('course_name'):
            course = self._escape_latex(essay_data.get('course_name'))
            lines.append("\\\\[0.5cm]")
            lines.append(course)

        # Date
        lines.append("\\\\[1cm]")
        lines.append("\\today")

        lines.append("\\end{center}")
        lines.append("\\vspace*{\\fill}")
        lines.append("\\newpage")
        lines.append("")

        return "\n".join(lines)

    def _build_mla_header(self, essay_data: Dict[str, Any]) -> str:
        """Build MLA header (no title page)."""

        lines = []

        # Student info (top left)
        lines.append(f"{self._escape_latex(essay_data.get('author', 'Student Name'))}")
        lines.append("\\\\")
        lines.append(f"{self._escape_latex(essay_data.get('instructor', 'Instructor Name'))}")
        lines.append("\\\\")
        lines.append(f"{self._escape_latex(essay_data.get('course_name', 'Course Name'))}")
        lines.append("\\\\")
        lines.append("\\today")
        lines.append("")

        # Title (centered)
        title = self._escape_latex(essay_data.get('title', 'Untitled Essay'))
        lines.append("\\begin{center}")
        lines.append(title)
        lines.append("\\end{center}")
        lines.append("")

        return "\n".join(lines)

    def _build_chicago_title_page(self, essay_data: Dict[str, Any]) -> str:
        """Build Chicago title page."""

        lines = []

        lines.append("\\vspace*{3cm}")

        # Title (centered)
        title = self._escape_latex(essay_data.get('title', 'Untitled Essay'))
        lines.append("\\begin{center}")
        lines.append(f"\\textbf{{{title}}}")
        lines.append("\\end{center}")

        lines.append("\\vspace*{3cm}")

        # "By"
        lines.append("\\begin{center}")
        lines.append("By")
        lines.append("\\\\[0.5cm]")

        # Author
        author = self._escape_latex(essay_data.get('author', 'Student Name'))
        lines.append(author)
        lines.append("\\\\[1cm]")

        # Course and institution
        if essay_data.get('course_name'):
            course = self._escape_latex(essay_data.get('course_name'))
            lines.append(course)
            lines.append("\\\\[0.5cm]")

        institution = self._escape_latex(essay_data.get('institution', 'University Name'))
        lines.append(institution)
        lines.append("\\\\[0.5cm]")

        # Date
        lines.append("\\today")
        lines.append("\\end{center}")

        lines.append("\\newpage")
        lines.append("")

        return "\n".join(lines)

    def _build_harvard_title_page(self, essay_data: Dict[str, Any]) -> str:
        """Build Harvard title page."""
        # Similar to generic
        return self._build_generic_title_page(essay_data)

    def _build_generic_title_page(self, essay_data: Dict[str, Any]) -> str:
        """Build generic title page."""

        lines = []

        # Use standard LaTeX title
        lines.append("\\maketitle")
        lines.append("\\newpage")
        lines.append("")

        return "\n".join(lines)

    def _build_content(
        self,
        essay_data: Dict[str, Any],
        template: str
    ) -> str:
        """Build main content section."""

        content = essay_data.get('content', '')

        if not content:
            return "\n(No content available)\n"

        lines = []

        # Split content into paragraphs
        paragraphs = content.split("\n\n")

        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            # Check if heading
            if para_text.startswith("#"):
                lines.append(self._convert_heading(para_text))
            else:
                # Regular paragraph
                escaped = self._escape_latex(para_text)
                lines.append(escaped)
                lines.append("")  # Blank line between paragraphs

        return "\n".join(lines)

    def _convert_heading(self, heading_text: str) -> str:
        """Convert markdown-style heading to LaTeX."""

        # Count heading level
        level = 0
        for char in heading_text:
            if char == "#":
                level += 1
            else:
                break

        # Extract text
        text = heading_text.lstrip("#").strip()
        text = self._escape_latex(text)

        # Map to LaTeX section command
        if level == 1:
            return f"\\section{{{text}}}"
        elif level == 2:
            return f"\\subsection{{{text}}}"
        elif level == 3:
            return f"\\subsubsection{{{text}}}"
        else:
            return f"\\paragraph{{{text}}}"

    def _build_references(
        self,
        essay_data: Dict[str, Any],
        template: str
    ) -> str:
        """Build references section."""

        lines = []

        # Section heading
        if template == "apa":
            lines.append("\\newpage")
            lines.append("\\section*{References}")
        elif template == "mla":
            lines.append("\\newpage")
            lines.append("\\begin{center}")
            lines.append("\\textbf{Works Cited}")
            lines.append("\\end{center}")
        elif template == "chicago":
            lines.append("\\newpage")
            lines.append("\\section*{Bibliography}")
        else:
            lines.append("\\newpage")
            lines.append("\\section*{References}")

        lines.append("")

        # Start bibliography environment
        lines.append("\\begin{thebibliography}{99}")
        lines.append("")

        # Add sources
        sources = essay_data.get('sources', [])

        for idx, source in enumerate(sources, 1):
            citation = self._format_citation(source, template)
            lines.append(f"\\bibitem{{ref{idx}}} {citation}")
            lines.append("")

        lines.append("\\end{thebibliography}")
        lines.append("")

        return "\n".join(lines)

    def _format_citation(
        self,
        source: Dict[str, Any],
        template: str
    ) -> str:
        """Format citation according to template style."""

        # Check for pre-formatted citation
        if template == "apa" and source.get("citation_apa"):
            return self._escape_latex(source["citation_apa"])
        elif template == "mla" and source.get("citation_mla"):
            return self._escape_latex(source["citation_mla"])
        elif template == "harvard" and source.get("citation_harvard"):
            return self._escape_latex(source["citation_harvard"])

        # Fallback: basic citation
        author = self._escape_latex(source.get("author", "Unknown Author"))
        year = source.get("year", "n.d.")
        title = self._escape_latex(source.get("title", "Untitled"))

        if template == "apa":
            return f"{author} ({year}). \\textit{{{title}}}."
        elif template == "mla":
            return f'{author}. ``{title}.\'\' {year}.'
        elif template == "harvard":
            return f"{author} ({year}) \\textit{{{title}}}."
        else:
            return f"{author} ({year}). \\textit{{{title}}}."

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""

        if not text:
            return ""

        # Special characters that need escaping
        replacements = {
            '\\': '\\textbackslash{}',
            '&': '\\&',
            '%': '\\%',
            '$': '\\$',
            '#': '\\#',
            '_': '\\_',
            '{': '\\{',
            '}': '\\}',
            '~': '\\textasciitilde{}',
            '^': '\\textasciicircum{}'
        }

        # Replace backslash first
        text = text.replace('\\', replacements['\\'])

        # Replace other special characters
        for char, replacement in replacements.items():
            if char != '\\':  # Already done
                text = text.replace(char, replacement)

        return text

    def _compile_latex(self, tex_file_path: str) -> Optional[str]:
        """
        Compile LaTeX file to PDF using pdflatex.

        Args:
            tex_file_path: Path to .tex file

        Returns:
            Path to compiled PDF, or None if compilation failed
        """
        import subprocess
        import shutil

        # Check if pdflatex is available
        if not shutil.which("pdflatex"):
            print("Warning: pdflatex not found. Cannot compile to PDF.")
            return None

        try:
            # Get directory and filename
            directory = os.path.dirname(tex_file_path)
            filename = os.path.basename(tex_file_path)

            # Run pdflatex twice (for references)
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", filename],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    print(f"LaTeX compilation warning (pass {_+1})")

            # Check if PDF was created
            pdf_path = tex_file_path.replace('.tex', '.pdf')
            if os.path.exists(pdf_path):
                return pdf_path
            else:
                return None

        except subprocess.TimeoutExpired:
            print("LaTeX compilation timed out")
            return None
        except Exception as e:
            print(f"LaTeX compilation failed: {e}")
            return None


def create_exporter() -> LaTeXExporter:
    """
    Factory function to create LaTeX exporter.

    Returns:
        LaTeXExporter instance
    """
    return LaTeXExporter()
