"""Read-only stage/provenance checks. Not a scientific or visual-fidelity validator."""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
STAGES = ['content', 'prompts', 'images', 'ppt']

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check(project, base, stage='content'):
    base = Path(base)
    errors, warnings = [], []
    def fail(msg): errors.append(msg)
    def file_at(value): return (base / value).resolve()
    def ids(rows, context):
        values = [r.get('id') for r in rows]
        if any(not isinstance(v,str) or not v.strip() for v in values):
            fail(context+': missing id')
        if len(set(values)) != len(values): fail(context+': duplicate ids')
        return set(values)
    sources = project.get('sources', [])
    references = project.get('references', [])
    source_ids = ids(sources, 'sources')
    reference_ids = ids(references, 'references')
    pages = project.get('pages', [])
    if not pages: fail('No pages')
    ids(pages, 'pages')
    for src in sources:
        if src.get('path'):
            fp = file_at(src['path'])
            if not fp.is_file(): fail('Missing source: '+str(fp))
            elif src.get('sha256') and digest(fp) != src['sha256']:
                fail('Source hash changed: '+src['id'])
        elif not src.get('url') and not src.get('text'):
            fail('Source has no path/url/text: '+str(src.get('id')))
    for r in references:
        if not str(r.get('url','')).startswith(('https://','http://')):
            fail('Reference lacks a source URL: '+str(r.get('id')))
    image_hashes = set()
    for page in pages:
        pid = str(page.get('id'))
        if not page.get('title') or not page.get('claim'): fail(pid+': title/claim required')
        if page.get('claim_status') not in {'established','proposed','illustrative'}:
            fail(pid+': invalid claim_status')
        if not page.get('source_ids'): fail(pid+': no raw source linkage')
        if set(page.get('source_ids',[]))-source_ids: fail(pid+': unknown source_ids')
        if set(page.get('reference_ids',[]))-reference_ids: fail(pid+': unknown reference_ids')
        nodes = ids(page.get('nodes',[]),pid+' nodes')
        ids(page.get('edges',[]),pid+' edges')
        for e in page.get('edges',[]):
            if e.get('from') not in nodes or e.get('to') not in nodes:
                fail(pid+': dangling edge '+str(e.get('id')))
            if not e.get('relation') or e.get('arrow') not in {'none','start','end','both'}:
                fail(pid+': edge semantics missing '+str(e.get('id')))
        if not page.get('text_runs'): fail(pid+': no canonical text')
        ids(page.get('text_runs',[]),pid+' text')
        for f in page.get('formulas',[]):
            if not f.get('canonical') or not f.get('definitions') or not f.get('assumptions'):
                fail(pid+': incomplete formula '+str(f.get('id')))
        if STAGES.index(stage)>=1:
            prompt = page.get('prompt') or {}
            fp = file_at(prompt.get('path',''))
            if not fp.is_file() or not fp.read_text(encoding='utf-8').strip():
                fail(pid+': missing written prompt')
        if STAGES.index(stage)>=2:
            img = page.get('image') or {}
            fp = file_at(img.get('path',''))
            if not fp.is_file(): fail(pid+': generated/provided image missing')
            else:
                actual = digest(fp)
                image_hashes.add(actual)
                if not img.get('sha256') or actual!=img['sha256']:
                    fail(pid+': image hash missing/changed')
            if not img.get('origin') or not img.get('prompt_path'):
                fail(pid+': image provenance incomplete')
            review = page.get('visual_review') or {}
            if not review.get('scientific_checked'):
                fail(pid+': scientific image review not recorded')
        if stage=='ppt':
            objs = page.get('ppt_objects') or []
            if not objs: fail(pid+': no object-level rebuild inventory')
            ids(objs,pid+' ppt_objects')
            for obj in objs:
                if obj.get('semantic_unit_count')!=1 and not obj.get('approved_scene_background'):
                    fail(pid+': multi-unit image/object '+str(obj.get('id')))
                if obj.get('kind') in {'text','shape','connector','plot'} and not str(obj.get('representation','')).startswith('native_'):
                    fail(pid+': structural/text object is not native '+str(obj.get('id')))
            review = page.get('visual_review') or {}
            if not review.get('ppt_render_checked'):
                fail(pid+': PPT render review not recorded')
    stats = []
    if stage=='ppt':
        ppt = project.get('ppt') or {}
        fp = file_at(ppt.get('path',''))
        if not fp.is_file(): fail('PPT file missing')
        else:
            try:
                with zipfile.ZipFile(fp) as z:
                    slides = sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],key=lambda n:int(re.search(r'(\d+)\.xml$',n)[1]))
                    if len(slides)!=len(pages): fail('Page/image-to-slide count mismatch')
                    pres=ET.fromstring(z.read('ppt/presentation.xml'))
                    size=pres.find('p:sldSz',NS)
                    area=int(size.get('cx'))*int(size.get('cy'))
                    for name in z.namelist():
                        if name.startswith('ppt/media/') and hashlib.sha256(z.read(name)).hexdigest() in image_hashes:
                            fail('Whole reference image embedded: '+name)
                    for i,(name,page) in enumerate(zip(slides,pages),1):
                        root=ET.fromstring(z.read(name))
                        shapes=root.findall('.//p:sp',NS)+root.findall('.//p:cxnSp',NS)
                        pics=root.findall('.//p:pic',NS)
                        mapping={}
                        for el in shapes+pics:
                            tag=el.find('.//p:cNvPr',NS)
                            if tag is not None: mapping[tag.get('name')]=el
                        for obj in page.get('ppt_objects',[]):
                            el=mapping.get(obj['id'])
                            if el is None:
                                fail(f'Slide {i}: missing object '+obj['id']);continue
                            if obj.get('representation','').startswith('native_') and el.tag.endswith('}pic'):
                                fail(f'Slide {i}: bitmap falsely declared native '+obj['id'])
                            if 'expected_text' in obj:
                                actual='\n'.join(''.join(t.text or '' for t in par.findall('.//a:t',NS)) for par in el.findall('.//a:p',NS))
                                if actual.strip()!=obj['expected_text'].strip(): fail(f'Slide {i}: text mismatch '+obj['id'])
                        for pic in pics:
                            ext=pic.find('.//a:xfrm/a:ext',NS)
                            if ext is not None and int(ext.get('cx'))*int(ext.get('cy'))/area>.85:
                                fail(f'Slide {i}: near-full-slide raster needs removal and object-level reconstruction')
                        stats.append({'slide':i,'native':len(shapes),'pictures':len(pics)})
            except (zipfile.BadZipFile,KeyError,ET.ParseError,TypeError,ValueError) as exc:
                fail('Cannot inspect PPT package: '+str(exc))
        warnings.append('Counts/hash/geometry checks do not prove scientific correctness or fidelity; inspect all slide renders and image coverage.')
    return {'passed':not errors,'stage':stage,'pages':len(pages),'errors':errors,'warnings':warnings,'ppt_counts':stats}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('project',type=Path)
    ap.add_argument('--stage',choices=STAGES,default='content')
    args=ap.parse_args()
    try:
        project=json.loads(args.project.read_text(encoding='utf-8'))
        result=check(project,args.project.resolve().parent,args.stage)
    except (OSError,ValueError,TypeError) as exc:
        result={'passed':False,'stage':args.stage,'errors':[str(exc)]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__': sys.exit(main())
