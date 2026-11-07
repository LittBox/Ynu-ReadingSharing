#!/usr/bin/env python3
"""Adapt HTML captures and original notes to image2ppt's image-PPTX input.

This file does not create the editable deliverable. It only serializes source
screenshots and lossless JSON note content for the skill's prepare command.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
HEADER = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
GROUP = '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
NS = f'xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"'


def rels(items):
    return HEADER + f'<Relationships xmlns="{REL}">' + ''.join(
        f'<Relationship Id="rId{i}" Type="{R}/{kind}" Target="{target}"/>'
        for i, kind, target in items
    ) + '</Relationships>'


def adapt(input_dir, notes_path, output):
    notes = json.loads(notes_path.read_text(encoding="utf-8"))
    assert isinstance(notes, list) and len(notes) == 30, "Expected original 30-page notes array"
    captures = [input_dir / f"page_{i:03d}.png" for i in range(1, len(notes) + 1)]
    dimensions = []
    for capture in captures:
        with capture.open("rb") as stream:
            header = stream.read(24)
        assert header[:8] == b"\x89PNG\r\n\x1a\n", f"Not a PNG: {capture}"
        dimensions.append(struct.unpack(">II", header[16:24]))
    assert len(set(dimensions)) == 1, "Source captures must share canvas dimensions"
    width, height = dimensions[0]
    cx, cy = width * 9525, height * 9525
    count = len(captures)
    content_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
    types = HEADER + f'<Types xmlns="{content_ns}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
    content_types = {
        "/ppt/presentation.xml": "presentation.main",
        "/ppt/slideMasters/slideMaster1.xml": "slideMaster",
        "/ppt/slideLayouts/slideLayout1.xml": "slideLayout",
        "/ppt/notesMasters/notesMaster1.xml": "notesMaster",
    }
    for i in range(1, count + 1):
        content_types[f"/ppt/slides/slide{i}.xml"] = "slide"
        content_types[f"/ppt/notesSlides/notesSlide{i}.xml"] = "notesSlide"
    types += ''.join(f'<Override PartName="{name}" ContentType="application/vnd.openxmlformats-officedocument.presentationml.{kind}+xml"/>' for name, kind in content_types.items()) + '</Types>'
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels([(1, "officeDocument", "ppt/presentation.xml")]))
        slides = ''.join(f'<p:sldId id="{255+i}" r:id="rId{i+2}"/>' for i in range(1, count + 1))
        z.writestr("ppt/presentation.xml", HEADER + f'<p:presentation {NS}><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>{slides}</p:sldIdLst><p:sldSz cx="{cx}" cy="{cy}"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>')
        z.writestr("ppt/_rels/presentation.xml.rels", rels([(1, "slideMaster", "slideMasters/slideMaster1.xml"), (2, "notesMaster", "notesMasters/notesMaster1.xml")] + [(i+2, "slide", f"slides/slide{i}.xml") for i in range(1, count+1)]))
        color_map = '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
        z.writestr("ppt/slideMasters/slideMaster1.xml", HEADER + f'<p:sldMaster {NS}><p:cSld><p:spTree>{GROUP}</p:spTree></p:cSld>{color_map}<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>')
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels([(1, "slideLayout", "../slideLayouts/slideLayout1.xml")]))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", HEADER + f'<p:sldLayout {NS} type="blank" preserve="1"><p:cSld><p:spTree>{GROUP}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([(1, "slideMaster", "../slideMasters/slideMaster1.xml")]))
        z.writestr("ppt/notesMasters/notesMaster1.xml", HEADER + f'<p:notesMaster {NS}><p:cSld><p:spTree>{GROUP}</p:spTree></p:cSld>{color_map}</p:notesMaster>')
        for i, (capture, note) in enumerate(zip(captures, notes), start=1):
            picture = f'<p:pic><p:nvPicPr><p:cNvPr id="2" name="Original HTML page {i}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
            z.writestr(f"ppt/slides/slide{i}.xml", HEADER + f'<p:sld {NS}><p:cSld><p:spTree>{GROUP}{picture}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels([(1, "slideLayout", "../slideLayouts/slideLayout1.xml"), (2, "image", f"../media/image{i}.png"), (3, "notesSlide", f"../notesSlides/notesSlide{i}.xml")]))
            z.write(capture, f"ppt/media/image{i}.png")
            # JSON retains every original key/value, list order and Unicode string.
            note_text = json.dumps(note, ensure_ascii=False, indent=2)
            paragraphs = ''.join(f'<a:p><a:r><a:t xml:space="preserve">{escape(line)}</a:t></a:r></a:p>' for line in note_text.split("\n"))
            body = '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Original speaker notes"/><p:cNvSpPr/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>' + paragraphs + '</p:txBody></p:sp>'
            z.writestr(f"ppt/notesSlides/notesSlide{i}.xml", HEADER + f'<p:notes {NS}><p:cSld><p:spTree>{GROUP}{body}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{i}.xml.rels", rels([(1, "notesMaster", "../notesMasters/notesMaster1.xml"), (2, "slide", f"../slides/slide{i}.xml")]))
    # Verify XML well-formedness, image identity and every original notes value.
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith((".xml", ".rels")):
                ET.fromstring(z.read(name))
        for i, (capture, note) in enumerate(zip(captures, notes), start=1):
            assert z.read(f"ppt/media/image{i}.png") == capture.read_bytes()
            root = ET.fromstring(z.read(f"ppt/notesSlides/notesSlide{i}.xml"))
            text = "\n".join("".join(n.text or "" for n in p.findall(f".//{{{A}}}t")) for p in root.findall(f".//{{{A}}}p"))
            assert json.loads(text) == note
    temporary.replace(output)
    print(json.dumps({"input_pptx": str(output), "pages": count, "notes_preserved": count, "canvas_px": [width, height], "purpose": "source-format adapter only"}, ensure_ascii=False))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=here / "input")
    parser.add_argument("--notes", type=Path, default=here.parent / "academic-delivery-test" / "演讲备注.json")
    parser.add_argument("--out", type=Path, default=here / "input" / "source-deck.pptx")
    args = parser.parse_args()
    adapt(args.input_dir, args.notes, args.out)
