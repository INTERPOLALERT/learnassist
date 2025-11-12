"""
Academic Command Center - Export Manager
Central coordinator for exporting essays to multiple formats.
"""

import logging
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from core.database import DatabaseManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ExportFormat:
    """Export format constants."""
    DOCX = "docx"
    PDF = "pdf"
    LATEX = "latex"
    MARKDOWN = "markdown"
    HTML = "html"
    TXT = "txt"


class ExportTemplate:
    """Template constants."""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    HARVARD = "harvard"
    GENERIC = "generic"


class ExportManager:
    """
    Central export coordinator.

    Features:
    - Export to multiple formats (DOCX, PDF, LaTeX, Markdown, HTML, TXT)
    - Template management (APA, MLA, Chicago, Harvard)
    - Export history tracking
    - Batch export support
    - Format validation
    """

    def __init__(self, user_id: str, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize export manager.

        Args:
            user_id: Current user ID
            db_manager: Database manager instance
        """
        self.user_id = user_id
        self.db = db_manager or DatabaseManager()

        # Lazy load exporters
        self._docx_exporter = None
        self._pdf_exporter = None
        self._latex_exporter = None
        self._markdown_exporter = None

        logger.info(f"Export manager initialized for user {user_id}")

    def export_essay(
        self,
        essay_id: str,
        format: str,
        template: Optional[str] = None,
        output_path: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export an essay to specified format.

        Args:
            essay_id: Essay ID to export
            format: Export format (docx, pdf, latex, markdown, html, txt)
            template: Template to use (apa, mla, chicago, harvard, generic)
            output_path: Output file path (auto-generated if not provided)
            options: Additional export options

        Returns:
            Result dictionary with success status and file path
        """
        try:
            # Get essay data
            essay_data = self._get_essay_data(essay_id)
            if not essay_data:
                return {
                    'success': False,
                    'error': 'Essay not found'
                }

            # Validate format
            if not self._validate_format(format):
                return {
                    'success': False,
                    'error': f'Unsupported format: {format}'
                }

            # Set default template if not provided
            if not template:
                template = ExportTemplate.GENERIC

            # Set default options
            if not options:
                options = {}

            # Generate output path if not provided
            if not output_path:
                output_path = self._generate_output_path(essay_data, format)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Route to appropriate exporter
            logger.info(f"Exporting essay {essay_id} to {format} format")

            if format == ExportFormat.DOCX:
                result = self._export_to_docx(essay_data, template, output_path, options)
            elif format == ExportFormat.PDF:
                result = self._export_to_pdf(essay_data, template, output_path, options)
            elif format == ExportFormat.LATEX:
                result = self._export_to_latex(essay_data, template, output_path, options)
            elif format == ExportFormat.MARKDOWN:
                result = self._export_to_markdown(essay_data, output_path, options)
            elif format == ExportFormat.HTML:
                result = self._export_to_html(essay_data, template, output_path, options)
            elif format == ExportFormat.TXT:
                result = self._export_to_txt(essay_data, output_path, options)
            else:
                return {
                    'success': False,
                    'error': f'Format {format} not yet implemented'
                }

            # Log export to database
            if result.get('success'):
                self._log_export(essay_id, format, template, result['file_path'])

            return result

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def batch_export(
        self,
        essay_ids: List[str],
        format: str,
        template: Optional[str] = None,
        output_dir: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export multiple essays at once.

        Args:
            essay_ids: List of essay IDs to export
            format: Export format
            template: Template to use
            output_dir: Output directory
            options: Export options

        Returns:
            Result with success count and failed exports
        """
        results = []
        successful = 0
        failed = []

        for essay_id in essay_ids:
            try:
                result = self.export_essay(essay_id, format, template, None, options)
                if result['success']:
                    successful += 1
                    results.append({
                        'essay_id': essay_id,
                        'file_path': result['file_path']
                    })
                else:
                    failed.append({
                        'essay_id': essay_id,
                        'error': result.get('error')
                    })
            except Exception as e:
                failed.append({
                    'essay_id': essay_id,
                    'error': str(e)
                })

        return {
            'success': True,
            'total': len(essay_ids),
            'successful': successful,
            'failed': len(failed),
            'results': results,
            'errors': failed
        }

    def get_export_history(
        self,
        essay_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get export history.

        Args:
            essay_id: Filter by essay ID (optional)
            limit: Maximum number of records

        Returns:
            Export history records
        """
        try:
            if essay_id:
                query = """
                SELECT id, essay_id, format, template, file_path, exported_at, file_size
                FROM export_history
                WHERE user_id = ? AND essay_id = ?
                ORDER BY exported_at DESC
                LIMIT ?
                """
                params = (self.user_id, essay_id, limit)
            else:
                query = """
                SELECT id, essay_id, format, template, file_path, exported_at, file_size
                FROM export_history
                WHERE user_id = ?
                ORDER BY exported_at DESC
                LIMIT ?
                """
                params = (self.user_id, limit)

            history = self.db.execute_query(query, params, fetch_all=True)

            return {
                'success': True,
                'history': history or [],
                'count': len(history) if history else 0
            }

        except Exception as e:
            logger.error(f"Failed to get export history: {e}")
            return {
                'success': False,
                'error': str(e),
                'history': []
            }

    def get_available_templates(self, format: str) -> List[str]:
        """
        Get available templates for a format.

        Args:
            format: Export format

        Returns:
            List of available template names
        """
        # Academic templates
        academic_templates = [
            ExportTemplate.APA,
            ExportTemplate.MLA,
            ExportTemplate.CHICAGO,
            ExportTemplate.HARVARD
        ]

        # Formats that support academic templates
        if format in [ExportFormat.DOCX, ExportFormat.PDF, ExportFormat.LATEX]:
            return academic_templates + [ExportTemplate.GENERIC]
        else:
            return [ExportTemplate.GENERIC]

    def validate_export(
        self,
        essay_id: str,
        format: str
    ) -> Dict[str, Any]:
        """
        Pre-export validation.

        Args:
            essay_id: Essay ID
            format: Export format

        Returns:
            Validation result with warnings/errors
        """
        issues = []
        warnings = []

        # Check essay exists
        essay_data = self._get_essay_data(essay_id)
        if not essay_data:
            issues.append("Essay not found")
            return {
                'valid': False,
                'issues': issues,
                'warnings': warnings
            }

        # Check content
        if not essay_data.get('content') or len(essay_data['content'].strip()) == 0:
            issues.append("Essay has no content")

        # Check format support
        if not self._validate_format(format):
            issues.append(f"Unsupported format: {format}")

        # Check file size (if large content)
        if essay_data.get('content') and len(essay_data['content']) > 1000000:
            warnings.append("Essay content is very large (>1MB)")

        # Format-specific checks
        if format == ExportFormat.PDF:
            # Check if required libraries available
            try:
                import reportlab
            except ImportError:
                warnings.append("reportlab not installed - PDF export may fail")

        if format == ExportFormat.DOCX:
            try:
                import docx
            except ImportError:
                issues.append("python-docx not installed - DOCX export unavailable")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

    def _get_essay_data(self, essay_id: str) -> Optional[Dict[str, Any]]:
        """Get essay data from database."""
        query = """
        SELECT id, user_id, title, content, created_at, updated_at
        FROM essays
        WHERE id = ? AND user_id = ?
        """

        essay = self.db.execute_query(
            query,
            (essay_id, self.user_id),
            fetch_one=True
        )

        return essay

    def _validate_format(self, format: str) -> bool:
        """Validate export format."""
        valid_formats = [
            ExportFormat.DOCX,
            ExportFormat.PDF,
            ExportFormat.LATEX,
            ExportFormat.MARKDOWN,
            ExportFormat.HTML,
            ExportFormat.TXT
        ]
        return format.lower() in valid_formats

    def _generate_output_path(
        self,
        essay_data: Dict[str, Any],
        format: str
    ) -> str:
        """Generate output file path."""
        # Create exports directory
        exports_dir = os.path.join("temp", "exports")
        os.makedirs(exports_dir, exist_ok=True)

        # Sanitize title for filename
        title = essay_data.get('title', 'untitled')
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.{format}"

        return os.path.join(exports_dir, filename)

    def _export_to_docx(
        self,
        essay_data: Dict[str, Any],
        template: str,
        output_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export to DOCX format."""
        # Lazy load DOCX exporter
        if not self._docx_exporter:
            from .docx_exporter import create_exporter
            self._docx_exporter = create_exporter()

        return self._docx_exporter.export(essay_data, output_path, template, options)

    def _export_to_pdf(
        self,
        essay_data: Dict[str, Any],
        template: str,
        output_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export to PDF format."""
        # Lazy load PDF exporter
        if not self._pdf_exporter:
            from .pdf_exporter import create_exporter
            self._pdf_exporter = create_exporter()

        return self._pdf_exporter.export(essay_data, output_path, template, options)

    def _export_to_latex(
        self,
        essay_data: Dict[str, Any],
        template: str,
        output_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export to LaTeX format."""
        # Lazy load LaTeX exporter
        if not self._latex_exporter:
            from .latex_exporter import LaTeXExporter
            self._latex_exporter = LaTeXExporter()

        return self._latex_exporter.export(essay_data, template, output_path, options)

    def _export_to_markdown(
        self,
        essay_data: Dict[str, Any],
        output_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export to Markdown format."""
        try:
            # Simple Markdown export
            content = f"# {essay_data.get('title', 'Untitled')}\n\n"
            content += essay_data.get('content', '')

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            file_size = os.path.getsize(output_path)

            return {
                'success': True,
                'file_path': output_path,
                'file_size': file_size,
                'format': ExportFormat.MARKDOWN
            }

        except Exception as e:
            logger.error(f"Markdown export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _export_to_html(
        self,
        essay_data: Dict[str, Any],
        template: str,
        output_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export to HTML format."""
        try:
            # Simple HTML export
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{essay_data.get('title', 'Untitled')}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
        }}
        p {{
            text-indent: 2em;
            text-align: justify;
        }}
    </style>
</head>
<body>
    <h1>{essay_data.get('title', 'Untitled')}</h1>
    <div class="content">
        {self._convert_to_html_paragraphs(essay_data.get('content', ''))}
    </div>
</body>
</html>"""

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            file_size = os.path.getsize(output_path)

            return {
                'success': True,
                'file_path': output_path,
                'file_size': file_size,
                'format': ExportFormat.HTML
            }

        except Exception as e:
            logger.error(f"HTML export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _export_to_txt(
        self,
        essay_data: Dict[str, Any],
        output_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export to plain text format."""
        try:
            content = f"{essay_data.get('title', 'Untitled')}\n"
            content += "=" * len(essay_data.get('title', 'Untitled')) + "\n\n"
            content += essay_data.get('content', '')

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            file_size = os.path.getsize(output_path)

            return {
                'success': True,
                'file_path': output_path,
                'file_size': file_size,
                'format': ExportFormat.TXT
            }

        except Exception as e:
            logger.error(f"TXT export failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _convert_to_html_paragraphs(self, text: str) -> str:
        """Convert plain text to HTML paragraphs."""
        paragraphs = text.split('\n\n')
        html_paragraphs = [f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()]
        return '\n'.join(html_paragraphs)

    def _log_export(
        self,
        essay_id: str,
        format: str,
        template: Optional[str],
        file_path: str
    ) -> None:
        """Log export to database."""
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

            query = """
            INSERT INTO export_history (
                id, user_id, essay_id, format, template,
                file_path, exported_at, file_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db.execute_query(
                query,
                (
                    str(uuid.uuid4()),
                    self.user_id,
                    essay_id,
                    format,
                    template,
                    file_path,
                    datetime.now().isoformat(),
                    file_size
                )
            )

            logger.info(f"Export logged: {essay_id} -> {format}")

        except Exception as e:
            logger.warning(f"Failed to log export: {e}")


if __name__ == "__main__":
    print("Testing Export Manager...")

    manager = ExportManager(user_id="test_user")

    # Test validation
    print("\n1. Testing format validation...")
    print(f"DOCX valid: {manager._validate_format('docx')}")
    print(f"PDF valid: {manager._validate_format('pdf')}")
    print(f"INVALID valid: {manager._validate_format('invalid')}")

    # Test available templates
    print("\n2. Testing available templates...")
    print(f"DOCX templates: {manager.get_available_templates('docx')}")
    print(f"Markdown templates: {manager.get_available_templates('markdown')}")

    # Test export (would need real essay)
    print("\n3. Export test skipped (requires real essay in database)")

    print("\nExport Manager validated!")
