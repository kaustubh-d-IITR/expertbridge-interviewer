from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class PDFGenerator:
    """
    Generates a PDF report for the interview.
    """
    def generate_report(self, analysis_data, filename="interview_report.pdf"):
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("ExpertBridge Interview Report", styles["Heading1"]))
            story.append(Spacer(1, 12))

            name = analysis_data.get("candidate_name", "Unknown Candidate")
            role = analysis_data.get("role", "Unknown Role")
            score = analysis_data.get("score", "N/A")
            
            story.append(Paragraph(f"<b>Candidate:</b> {name}", styles["Normal"]))
            story.append(Paragraph(f"<b>Role:</b> {role}", styles["Normal"]))
            story.append(Paragraph(f"<b>Overall Score:</b> {score}/100", styles["Normal"]))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph("<b>Executive Summary:</b>", styles["Heading2"]))
            summary = analysis_data.get("summary", "No summary available.")
            story.append(Paragraph(summary, styles["Normal"]))
            
            doc.build(story)
            print(f"[PDFGenerator] Report generated: {filename}")
            return filename
        except Exception as e:
            print(f"[PDFGenerator] Error generating PDF: {e}")
            return None
