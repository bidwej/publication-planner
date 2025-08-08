"""
PDF generator for timeline charts and reports.
"""

import os
from datetime import date
from pathlib import Path
from typing import Dict, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.core.models import Config
from app.components.charts.gantt_chart import create_gantt_chart, generate_gantt_png


class TimelinePDFGenerator:
    """Generate PDF reports for timeline charts."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.styles.add(ParagraphStyle(
            name='Title',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12
        ))
    
    def generate_timeline_pdf(
        self,
        schedule: Dict[str, date],
        config: Config,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a PDF report for the timeline.
        
        Args:
            schedule: Schedule dictionary
            config: Configuration object
            filename: Optional filename for the PDF
            
        Returns:
            Path to the generated PDF file
        """
        if not filename:
            timestamp = date.today().strftime("%Y%m%d")
            filename = f"timeline_report_{timestamp}.pdf"
        
        pdf_path = self.output_dir / filename
        
        # Generate the Gantt chart PNG
        chart_filename = "timeline_chart.png"
        chart_path = self.output_dir / chart_filename
        
        # Create the chart
        fig = create_gantt_chart(schedule, config)
        
        # Save as PNG
        try:
            fig.write_image(
                str(chart_path),
                width=1200,
                height=800,
                scale=2,
                format='png'
            )
        except Exception as e:
            print(f"Warning: Could not save chart as PNG: {e}")
            # Fallback: try to save as HTML and convert
            chart_path = None
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Paper Submission Timeline Report", self.styles['Title']))
        story.append(Spacer(1, 20))
        
        # Subtitle with date
        story.append(Paragraph(
            f"Generated on {date.today().strftime('%B %d, %Y')}",
            self.styles['Subtitle']
        ))
        story.append(Spacer(1, 30))
        
        # Summary information
        story.extend(self._create_summary_section(schedule, config))
        story.append(Spacer(1, 20))
        
        # Timeline chart
        if chart_path and chart_path.exists():
            story.extend(self._create_chart_section(chart_path))
            story.append(Spacer(1, 20))
        
        # Schedule details
        story.extend(self._create_schedule_details(schedule, config))
        story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF report generated: {pdf_path}")
        return str(pdf_path)
    
    def _create_summary_section(self, schedule: Dict[str, date], config: Config) -> list:
        """Create summary section of the PDF."""
        story = []
        
        story.append(Paragraph("Summary", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Calculate summary statistics
        total_submissions = len(schedule)
        if schedule:
            start_date = min(schedule.values())
            end_date = max(schedule.values())
            duration_days = (end_date - start_date).days
        else:
            start_date = end_date = date.today()
            duration_days = 0
        
        # Create summary table
        summary_data = [
            ["Metric", "Value"],
            ["Total Submissions", str(total_submissions)],
            ["Timeline Start", start_date.strftime("%B %d, %Y")],
            ["Timeline End", end_date.strftime("%B %d, %Y")],
            ["Duration", f"{duration_days} days"],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_chart_section(self, chart_path: Path) -> list:
        """Create chart section of the PDF."""
        story = []
        
        story.append(Paragraph("Timeline Visualization", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Add the chart image
        img = Image(str(chart_path), width=6*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 12))
        
        # Add chart description
        story.append(Paragraph(
            "The timeline chart above shows the schedule of paper submissions and work items. "
            "Color coding indicates the type of submission (engineering vs medical) and "
            "whether it's a paper or work item. Light gray bands represent blackout periods "
            "and time intervals for better readability.",
            self.styles['BodyText']
        ))
        
        return story
    
    def _create_schedule_details(self, schedule: Dict[str, date], config: Config) -> list:
        """Create detailed schedule section."""
        story = []
        
        story.append(Paragraph("Schedule Details", self.styles['Heading2']))
        story.append(Spacer(1, 12))
        
        if not schedule:
            story.append(Paragraph("No schedule data available.", self.styles['BodyText']))
            return story
        
        # Sort schedule by date
        sorted_schedule = sorted(schedule.items(), key=lambda x: x[1])
        
        # Create schedule table
        table_data = [["Submission", "Start Date", "Type", "Conference"]]
        
        for submission_id, start_date in sorted_schedule:
            submission = config.submissions_dict.get(submission_id)
            if submission:
                submission_type = "Paper" if submission.kind.value == "paper" else "Work"
                conference_name = "N/A"
                if submission.conference_id:
                    conference = config.conferences_dict.get(submission.conference_id)
                    if conference:
                        conference_name = conference.name
                
                table_data.append([
                    submission.title or submission_id,
                    start_date.strftime("%B %d, %Y"),
                    submission_type,
                    conference_name
                ])
        
        schedule_table = Table(table_data, colWidths=[2*inch, 1.5*inch, 1*inch, 2.5*inch])
        schedule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white])
        ]))
        
        story.append(schedule_table)
        
        return story


def generate_timeline_pdf(
    schedule: Dict[str, date],
    config: Config,
    output_dir: str = "reports",
    filename: Optional[str] = None
) -> str:
    """
    Generate a PDF report for the timeline.
    
    Args:
        schedule: Schedule dictionary
        config: Configuration object
        output_dir: Directory to save the PDF
        filename: Optional filename for the PDF
        
    Returns:
        Path to the generated PDF file
    """
    generator = TimelinePDFGenerator(output_dir)
    return generator.generate_timeline_pdf(schedule, config, filename)
