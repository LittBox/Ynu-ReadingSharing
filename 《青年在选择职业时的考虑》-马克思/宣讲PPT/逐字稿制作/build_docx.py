from pathlib import Path
import json, re
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path('/Users/admin/Desktop/云上书屋/宣讲PPT')
WORK = ROOT / '逐字稿制作'
OUT = ROOT / '第一份工作，只是起点_逐字稿.docx'
source = (WORK / '稿件.txt').read_text()
notes = json.loads((ROOT / 'academic-delivery-test' / '演讲备注.json').read_text())
sections = re.split(r'^## ', source, flags=re.M)[1:]
assert len(sections) == len(notes) == 30
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.top_margin, sec.bottom_margin = Mm(20), Mm(19)
sec.left_margin, sec.right_margin = Mm(23), Mm(23)
sec.footer_distance = Mm(9)

def font(style, size, bold=False, color='000000'):
    style.font.name = 'Source Han Sans SC'
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor.from_string(color)
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)
    for key in list(rf.attrib):
        if 'theme' in key.lower():
            del rf.attrib[key]
    for a in ['ascii','hAnsi','eastAsia','cs']:
        rf.set(qn('w:'+a), 'Source Han Sans SC')
    lang = OxmlElement('w:lang')
    lang.set(qn('w:val'),'zh-CN')
    lang.set(qn('w:eastAsia'),'zh-CN')
    rpr.append(lang)

font(doc.styles['Normal'], 13)
norm = doc.styles['Normal'].paragraph_format
norm.line_spacing = Pt(21)
norm.space_after = Pt(7)
norm.widow_control = True
norm.keep_together = True
font(doc.styles['Title'], 23, True)
doc.styles['Title'].paragraph_format.space_after = Pt(6)
doc.styles['Title'].paragraph_format.line_spacing = Pt(30)
font(doc.styles['Subtitle'], 12)
doc.styles['Subtitle'].paragraph_format.space_after = Pt(7)
font(doc.styles['Heading 1'], 15, True)
h = doc.styles['Heading 1'].paragraph_format
h.space_before, h.space_after = Pt(15), Pt(3)
h.line_spacing = Pt(22)
h.keep_with_next = True
for name,size,color in [('Timing',10,'444444'),('Cue',11,'555555'),('Instructions',10.5,'000000')]:
    st=doc.styles.add_style(name,1)
    font(st,size,color=color)
    st.paragraph_format.line_spacing=Pt(17)
    st.paragraph_format.space_after=Pt(6)
    st.paragraph_format.keep_together=True
doc.styles['Timing'].paragraph_format.keep_with_next=True
doc.styles['Cue'].paragraph_format.left_indent=Mm(4)
for st in doc.styles:
    for border in list(st.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
doc.add_paragraph('第一份工作 只是起点',style='Title')
doc.add_paragraph('宣讲逐字稿  曾湘雨',style='Subtitle')
doc.add_paragraph('与30页PPT逐页对应，预计45分钟，含互动和停顿。方括号内为现场提示，不朗读。各页时间供排练参考，可随现场语速微调。',style='Instructions')

def stamp(seconds):
    return f'{int(seconds)//60:02d}:{int(seconds)%60:02d}'
elapsed=0
spoken=[]
for idx,(block,note) in enumerate(zip(sections,notes),1):
    heading, body = block.split('\n',1)
    title=heading.split(' ',1)[1]
    doc.add_paragraph(f'PPT {idx:02d}  {title}',style='Heading 1')
    secs=int(note['minutes']*60)
    duration=f'{secs//60}分{secs%60:02d}秒' if secs%60 else f'{secs//60}分钟'
    doc.add_paragraph(f'{stamp(elapsed)}—{stamp(elapsed+secs)}  ·  本页约{duration}',style='Timing')
    elapsed+=secs
    for text in re.split(r'\n\s*\n',body.strip()):
        text=text.strip()
        if not text: continue
        style='Cue' if text.startswith('【') else 'Normal'
        doc.add_paragraph(text,style=style)
        if style=='Normal': spoken.append(text)

footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
footer.paragraph_format.space_after=Pt(0)
run=footer.add_run()
run.font.name='Source Han Sans SC'
run.font.size=Pt(10)
run.font.color.rgb=RGBColor.from_string('555555')
field=OxmlElement('w:fldSimple'); field.set(qn('w:instr'),'PAGE'); run._r.addnext(field)
doc.core_properties.title='第一份工作 只是起点 宣讲逐字稿'
doc.core_properties.subject='与30页宣讲PPT对应的45分钟演讲稿'
doc.core_properties.author='曾湘雨'
doc.core_properties.keywords='青年择业 马克思 青年在选择职业时的考虑'
doc.core_properties.comments=''
doc.save(OUT)
print(json.dumps({'output':str(OUT),'slides':len(sections),'minutes':elapsed/60,'spoken_characters':len(re.findall(r'[\u4e00-\u9fff0-9A-Za-z]',''.join(spoken)))},ensure_ascii=False))
