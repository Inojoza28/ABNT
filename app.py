from flask import Flask, render_template, request, send_file
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from datetime import datetime
import io

app = Flask(__name__, static_folder='static')
app.secret_key = 'supersecretkey'

# ========== VALIDAÇÃO ==========
REQUIRED_FIELDS = [
    'title', 'author', 'institution', 'course', 
    'abstract', 'introducao', 'body', 'conclusao', 'references'
]

def validate_inputs(form_data):
    errors = {}
    for field in REQUIRED_FIELDS:
        if not form_data.get(field, '').strip():
            errors[field] = 'Campo obrigatório'
    return errors if errors else None

# ========== GERADOR ABNT ==========
def configure_document_styles(doc):
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(12)
    paragraph_format = style.paragraph_format
    paragraph_format.line_spacing = 1.5
    paragraph_format.first_line_indent = Cm(1.25)  # Recuo ABNT
    paragraph_format.space_after = Pt(0)

def create_header(section, title):
    header = section.header.paragraphs[0]
    header.text = title[:50]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.style.font.size = Pt(10)

def create_cover(doc, data):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    title = p.add_run(f"\n\n{data['title'].upper()}\n")
    title.font.size = Pt(16)
    title.bold = True
    
    p.add_run(f"\n{data['author']}\n").font.size = Pt(14)
    
    institution = p.add_run(
        f"\n\n{data['institution']}\n"
        f"{data['course']}\n"
        f"{datetime.now().strftime('%B de %Y')}"
    )
    institution.font.size = Pt(12)

def format_section(doc, title, content, is_main_text=True):
    # Título sem recuo
    title_para = doc.add_paragraph(title)
    title_para.style = 'Heading2'
    title_para.bold = True
    title_para.paragraph_format.first_line_indent = Cm(0)
    
    # Conteúdo com recuo
    for paragraph in content.split('\n\n'):
        if paragraph.strip():
            p = doc.add_paragraph(paragraph.strip())
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            if is_main_text:
                p.paragraph_format.first_line_indent = Cm(1.25)

def create_abnt_document(form_data):
    doc = Document()
    
    # Configuração da página
    section = doc.sections[0]
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)
    
    configure_document_styles(doc)
    create_header(section, form_data.get('short_title', form_data['title']))
    create_cover(doc, form_data)
    doc.add_page_break()
    
    # Seções principais
    sections = [
        ("RESUMO", form_data['abstract'], False),  # Sem recuo
        ("INTRODUÇÃO", form_data['introducao']),
        ("DESENVOLVIMENTO", form_data['body']),
        ("CONCLUSÃO", form_data['conclusao'])
    ]
    
    for title, content, *flags in sections:
        format_section(doc, title, content, is_main_text=(False if flags else True))
        doc.add_page_break()
    
    # Referências
    doc.add_paragraph("REFERÊNCIAS").style = 'Heading1'
    for ref in form_data['references'].split('\n'):
        if ref.strip():
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1.25)
            p.paragraph_format.first_line_indent = Cm(-1.25)
            p.add_run(ref.strip()).font.name = 'Arial'
    
    # Página final em branco
    doc.add_page_break()
    last_para = doc.add_paragraph()
    last_para.add_run("\n").font.size = Pt(12)
    
    return doc

# ========== ROTAS ==========
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        form_data = request.form.to_dict()
        errors = validate_inputs(form_data)
        
        if errors:
            return render_template('index.html', errors=errors, form_data=form_data)
        
        try:
            buffer = io.BytesIO()
            create_abnt_document(form_data).save(buffer)
            buffer.seek(0)
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"Documento_ABNT_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        except Exception as e:
            return render_template('index.html', error=str(e), form_data=form_data)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)