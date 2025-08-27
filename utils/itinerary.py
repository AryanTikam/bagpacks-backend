import subprocess
import tempfile
import os
import io
import re
from datetime import datetime, timedelta
from PIL import Image as PILImage
import requests

def fetch_static_map(places, width=600, height=350):
    marker_strs = []
    for i, place in enumerate(places):
        lat, lon = place.get("coords", [None, None])
        if lat is not None and lon is not None:
            color = "red" if i == 0 else "blue"
            marker_strs.append(f"markers={lat},{lon},{color}{i+1}")
    
    if not marker_strs:
        return None
        
    markers = "&".join(marker_strs)
    center = f"{places[0]['coords'][0]},{places[0]['coords'][1]}"
    
    # Try multiple map services
    map_urls = [
        f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/{center},{13}/{width}x{height}?access_token=pk.your_token",
        f"https://maps.googleapis.com/maps/api/staticmap?center={center}&zoom=13&size={width}x{height}&{markers}",
        f"https://staticmap.openstreetmap.de/staticmap.php?center={center}&zoom=13&size={width}x{height}&{markers}"
    ]
    
    for url in map_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Map service failed: {e}")
            continue
    
    print("All map services failed, continuing without map")
    return None

def markdown_to_latex(markdown_text):
    """Convert markdown to LaTeX with proper formatting for headers, bold, etc."""
    lines = markdown_text.split('\n')
    latex_content = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                latex_content.append('\\end{itemize}')
                in_list = False
            latex_content.append('\\vspace{0.5em}')
            continue
            
        # Escape special LaTeX characters
        escaped_line = line.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#')
        escaped_line = escaped_line.replace('_', '\\_').replace('{', '\\{').replace('}', '\\}')
        
        # Handle headers
        if line.startswith('# '):
            if in_list:
                latex_content.append('\\end{itemize}')
                in_list = False
            escaped_line = escaped_line[2:].strip()
            latex_content.append(f'\\section{{{handle_bold_text(escaped_line)}}}')
        elif line.startswith('## '):
            if in_list:
                latex_content.append('\\end{itemize}')
                in_list = False
            escaped_line = escaped_line[3:].strip()
            latex_content.append(f'\\subsection{{{handle_bold_text(escaped_line)}}}')
        elif line.startswith('### '):
            if in_list:
                latex_content.append('\\end{itemize}')
                in_list = False
            escaped_line = escaped_line[4:].strip()
            latex_content.append(f'\\subsubsection{{{handle_bold_text(escaped_line)}}}')
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                latex_content.append('\\begin{itemize}')
                in_list = True
            escaped_line = escaped_line[2:].strip()
            latex_content.append(f'\\item {handle_bold_text(escaped_line)}')
        else:
            if in_list:
                latex_content.append('\\end{itemize}')
                in_list = False
            latex_content.append(f'{handle_bold_text(escaped_line)}\\\\')
    
    if in_list:
        latex_content.append('\\end{itemize}')
    
    return '\n'.join(latex_content)

def handle_bold_text(text):
    """Handle **bold** and *italic* markdown formatting"""
    # Handle **bold** text
    text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', text)
    
    # Handle *italic* text (but not if it's part of **bold**)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\\textit{\1}', text)
    
    return text

def get_template_config(template_id):
    """Get template-specific configurations"""
    templates = {
        'modern': {
            'name': 'Modern Professional',
            'primary': '0.15, 0.39, 0.92',      # #2563eb
            'secondary': '0.49, 0.23, 0.93',    # #7c3aed  
            'accent': '0.02, 0.59, 0.41',       # #059669
            'geometry': 'top=2cm, bottom=2cm, left=2.5cm, right=2.5cm',
            'font_package': '\\usepackage{lmodern}',
            'header_style': 'modern',
            'background': 'none'
        },
        'vintage': {
            'name': 'Vintage Explorer',
            'primary': '0.57, 0.25, 0.05',      # #92400e
            'secondary': '0.71, 0.32, 0.04',    # #b45309
            'accent': '0.02, 0.37, 0.27',       # #065f46
            'geometry': 'top=2.5cm, bottom=2.5cm, left=3cm, right=3cm',
            'font_package': '\\usepackage{mathptmx}',
            'header_style': 'vintage',
            'background': 'vintage'
        },
        'minimalist': {
            'name': 'Minimalist Zen',
            'primary': '0.22, 0.25, 0.32',      # #374151
            'secondary': '0.42, 0.45, 0.50',    # #6b7280
            'accent': '0.05, 0.65, 0.91',       # #0ea5e9
            'geometry': 'top=2cm, bottom=2cm, left=2cm, right=2cm',
            'font_package': '\\usepackage{helvet}\\renewcommand{\\familydefault}{\\sfdefault}',
            'header_style': 'minimalist',
            'background': 'none'
        }
    }
    return templates.get(template_id, templates['modern'])

def generate_latex_template(destination, date_range, budget, people, days, itinerary_content, map_image_path=None, template_id='modern'):
    """Generate LaTeX template with the selected theme"""
    
    template_config = get_template_config(template_id)
    
    map_section = ""
    if map_image_path:
        map_section = f"""
\\section{{Route Map}}
\\begin{{center}}
\\includegraphics[width=0.8\\textwidth]{{map.png}}
\\end{{center}}
\\vspace{{1em}}
"""

    # Simplified but effective LaTeX template with proper color usage
    latex_template = f"""
\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{geometry}}
\\usepackage{{graphicx}}
\\usepackage{{xcolor}}
\\usepackage{{titling}}
\\usepackage{{fancyhdr}}
\\usepackage{{tcolorbox}}
\\usepackage{{enumitem}}
\\usepackage{{setspace}}
\\usepackage{{parskip}}
{template_config['font_package']}

% Page geometry
\\geometry{{
    {template_config['geometry']},
    headheight=1.5cm,
    headsep=0.5cm
}}

% Define colors
\\definecolor{{primary}}{{rgb}}{{{template_config['primary']}}}
\\definecolor{{secondary}}{{rgb}}{{{template_config['secondary']}}}
\\definecolor{{accent}}{{rgb}}{{{template_config['accent']}}}
\\definecolor{{lightgray}}{{rgb}}{{0.95, 0.95, 0.95}}
\\definecolor{{darkgray}}{{rgb}}{{0.3, 0.3, 0.3}}

% Title styling
\\title{{
    {{\\color{{primary}}\\Huge\\bfseries Travel Itinerary}}\\\\
    {{\\color{{secondary}}\\Large {destination} Adventure}}
}}
\\date{{}}
\\author{{}}

% Header and footer
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{\\color{{primary}}\\textbf{{Bagpack Travel Itinerary}}}}
\\fancyhead[R]{{\\color{{secondary}}{destination}}}
\\fancyfoot[C]{{\\color{{darkgray}}\\thepage}}
\\renewcommand{{\\headrulewidth}}{{2pt}}
\\renewcommand{{\\headrule}}{{\\color{{primary}}\\hrule height \\headrulewidth}}

% Section styling based on template
\\usepackage{{titlesec}}
""" + ("""
\\titleformat{\\section}
  {\\normalfont\\Large\\bfseries\\color{primary}}
  {\\thesection}{1em}{}
  [\\color{primary}\\titlerule]
""" if template_id == 'modern' else """
\\titleformat{\\section}
  {\\normalfont\\Large\\bfseries\\color{primary}}
  {\\thesection}{1em}{}
  [\\color{secondary}\\rule{\\textwidth}{2pt}]
""" if template_id == 'vintage' else """
\\titleformat{\\section}
  {\\normalfont\\Large\\bfseries\\color{primary}}
  {}{0em}{}
  [\\vspace{0.2em}\\color{primary}\\rule{\\textwidth}{0.5pt}\\vspace{0.3em}]
""") + f"""

\\titleformat{{\\subsection}}
  {{\\normalfont\\large\\bfseries\\color{{secondary}}}}
  {{\\thesubsection}}{{1em}}{{}}
\\titleformat{{\\subsubsection}}
  {{\\normalfont\\normalsize\\bfseries\\color{{accent}}}}
  {{\\thesubsubsection}}{{1em}}{{}}

% Custom info box
\\newtcolorbox{{infobox}}{{
    colback=lightgray,
    colframe=primary,
    boxrule=3pt,
    arc=8pt,
    left=15pt,
    right=15pt,
    top=15pt,
    bottom=15pt
}}

\\begin{{document}}

\\maketitle
\\thispagestyle{{fancy}}

% Trip Overview Box
\\begin{{infobox}}
\\begin{{center}}
\\textbf{{\\Large \\color{{primary}} Trip Overview}}
\\end{{center}}
\\vspace{{0.5em}}

\\noindent\\textbf{{\\color{{primary}}Destination:}} \\color{{darkgray}}{destination}\\\\
\\textbf{{\\color{{secondary}}Duration:}} \\color{{darkgray}}{days} {'day' if days == 1 else 'days'} ({date_range})\\\\
\\textbf{{\\color{{accent}}Travelers:}} \\color{{darkgray}}{people} {'person' if people == '1' else 'people'}\\\\
\\textbf{{\\color{{primary}}Budget:}} \\color{{darkgray}}₹{budget}\\\\
\\textbf{{\\color{{secondary}}Generated:}} \\color{{darkgray}}{datetime.now().strftime('%B %d, %Y at %I:%M %p')}
\\end{{infobox}}

\\vspace{{1em}}

{map_section}

% Main Content
{itinerary_content}

\\vspace{{2em}}

% Footer section
\\begin{{center}}
\\color{{darkgray}}
\\rule{{0.8\\textwidth}}{{0.5pt}}\\\\
\\vspace{{0.5em}}
\\textit{{Generated by Bagpack AI Travel Assistant}}\\\\
\\textit{{Template: \\color{{primary}}{template_config['name']}}}\\\\
\\textit{{Have a wonderful journey!}}
\\end{{center}}

\\end{{document}}
"""
    return latex_template

def create_itinerary_pdf(markdown_text, places=None, options=None, template_id='modern'):
    """Create PDF using LaTeX with the selected template"""
    
    # Extract information
    destination = "Your Destination"
    if places and len(places) > 0:
        destination = places[0].get('name', 'Your Destination').split(',')[0].strip()
    
    # Create date range
    start_date = datetime.now()
    days = 3  # default
    if options and options.get('days'):
        try:
            days = int(options['days'])
        except (ValueError, TypeError):
            days = 3
    
    end_date = start_date + timedelta(days=days-1)
    date_range = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    
    # Budget and people info
    budget = "Not specified"
    people = "1"
    if options:
        if options.get('budget'):
            budget = f"{options['budget']:,}"
        if options.get('people'):
            people = str(options['people'])
    
    # Convert markdown to LaTeX
    latex_content = markdown_to_latex(markdown_text)
    
    # Handle map image
    map_image_path = None
    temp_map_file = None
    if places and len(places) > 0:
        map_data = fetch_static_map(places)
        if map_data:
            temp_map_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_map_file.write(map_data)
            temp_map_file.close()
            map_image_path = temp_map_file.name
    
    # Generate LaTeX document with selected template
    latex_doc = generate_latex_template(
        destination, date_range, budget, people, days, 
        latex_content, map_image_path, template_id
    )
    
    print(f"Attempting to generate PDF with template: {template_id}")
    
    # Check if pdflatex is available
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write LaTeX file with UTF-8 encoding
            latex_file = os.path.join(temp_dir, "itinerary.tex")
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_doc)
            
            print(f"pdflatex found, proceeding with LaTeX compilation")
            print(f"LaTeX file written to: {latex_file}")
            
            # Copy map image if exists
            if map_image_path:
                map_dest = os.path.join(temp_dir, "map.png")
                import shutil
                shutil.copy2(map_image_path, map_dest)
            
            # Run pdflatex with proper encoding settings and error handling
            print("LaTeX compilation pass 1")
            result = subprocess.run([
                'pdflatex', 
                '-interaction=nonstopmode',
                '-output-directory=' + temp_dir,
                '-jobname=itinerary',
                latex_file
            ], 
            cwd=temp_dir,
            capture_output=True,
            text=True,  # This ensures text mode
            encoding='utf-8',  # Explicit UTF-8 encoding
            errors='replace',  # Replace invalid characters instead of failing
            timeout=30
            )
            
            # Check if PDF was created successfully
            pdf_file = os.path.join(temp_dir, "itinerary.pdf")
            if os.path.exists(pdf_file):
                print("PDF generated successfully")
                # Read PDF and return as BytesIO
                with open(pdf_file, 'rb') as f:
                    pdf_buffer = io.BytesIO(f.read())
                
                # Clean up temp map file
                if temp_map_file:
                    try:
                        os.unlink(temp_map_file.name)
                    except:
                        pass
                
                return pdf_buffer
            else:
                print(f"LaTeX compilation failed")
                print(f"stdout: {result.stdout}")
                print(f"stderr: {result.stderr}")
                print(f"return code: {result.returncode}")
                # Fall back to simple PDF
                return create_simple_pdf_fallback(markdown_text, places, template_id)
                
    except subprocess.TimeoutExpired:
        print("LaTeX compilation timed out, falling back to simple PDF")
        return create_simple_pdf_fallback(markdown_text, places, template_id)
    except (subprocess.CalledProcessError, FileNotFoundError, UnicodeDecodeError) as e:
        print(f"LaTeX compilation error: {e}")
        return create_simple_pdf_fallback(markdown_text, places, template_id)
    finally:
        # Clean up temp map file
        if temp_map_file:
            try:
                os.unlink(temp_map_file.name)
            except:
                pass

def clean_text_for_reportlab(text):
    """Clean markdown text for reportlab processing"""
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Fix double asterisks (bold) - ensure proper closing
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<b>\1</b>', text)
    
    # Fix single asterisks (italic)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
    
    # Remove list markers
    text = re.sub(r'^[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
    
    # Clean up any remaining markdown
    text = re.sub(r'[`~]', '', text)
    
    # Escape ampersands that aren't part of HTML entities
    text = re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', text)
    
    return text

def create_simple_pdf_fallback(markdown_text, places=None, template_id='modern'):
    """Improved fallback PDF generation using reportlab"""
    print(f"Using fallback PDF generation with reportlab - template: {template_id}")
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Get template colors
        template_config = get_template_config(template_id)
        
        # Convert RGB string to color object
        def rgb_string_to_color(rgb_str):
            r, g, b = map(float, rgb_str.split(', '))
            return colors.Color(r, g, b)
        
        primary_color = rgb_string_to_color(template_config['primary'])
        secondary_color = rgb_string_to_color(template_config['secondary'])
        
        # Create document
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=primary_color,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=secondary_color,
            leftIndent=0
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        # Story container
        story = []
        
        # Title
        destination = "Your Destination"
        if places and len(places) > 0:
            destination = places[0].get('name', 'Your Destination').split(',')[0].strip()
        
        story.append(Paragraph(f"Travel Itinerary", title_style))
        story.append(Paragraph(f"{destination} Adventure", heading_style))
        story.append(Spacer(1, 12))
        
        # Template info
        story.append(Paragraph(f"<b>Template:</b> {template_config['name']}", normal_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
        story.append(Spacer(1, 20))
        
        # Content
        cleaned_text = clean_text_for_reportlab(markdown_text)
        
        # Split into paragraphs and process
        paragraphs = cleaned_text.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                # Check if it's a heading (starts with #)
                if para.strip().startswith('#'):
                    heading_text = re.sub(r'^#+\s*', '', para.strip())
                    story.append(Paragraph(heading_text, heading_style))
                else:
                    story.append(Paragraph(para.strip(), normal_style))
                story.append(Spacer(1, 6))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Generated by Bagpack AI Travel Assistant", footer_style))
        story.append(Paragraph("Have a wonderful journey!", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except ImportError:
        print("reportlab not available, creating simple text-based PDF")
        return create_minimal_pdf_fallback(markdown_text, template_id)
    except Exception as e:
        print(f"Fallback PDF generation failed: {e}")
        return create_minimal_pdf_fallback(markdown_text, template_id)

def create_minimal_pdf_fallback(markdown_text, template_id='modern'):
    """Absolute minimal fallback - just return the text"""
    print("Creating minimal fallback response")
    buffer = io.BytesIO()
    
    # Create a very simple text response
    simple_content = f"""
TRAVEL ITINERARY - {template_id.upper()} TEMPLATE
Generated by Bagpack AI Travel Assistant
{datetime.now().strftime('%B %d, %Y at %I:%M %p')}

{markdown_text}

Have a wonderful journey!
""".encode('utf-8')
    
    buffer.write(simple_content)
    buffer.seek(0)
    return buffer

# Remove the DOCX function entirely
def create_itinerary_docx(*args, **kwargs):
    """DOCX generation is no longer supported"""
    raise NotImplementedError("DOCX generation has been removed. Use PDF with LaTeX instead.")