"""Behavioral checks for stage gates and dishonest full-slide-image packages."""
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from check_pipeline import check, digest

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        (self.root/'notes.txt').write_text('User research notes',encoding='utf-8')
        (self.root/'prompt.md').write_text('Exact labels, formulas, nodes, directed edges, layout and checks.',encoding='utf-8')
        self.project={'sources':[{'id':'notes','path':'notes.txt'}],'references':[], 'pages':[{
            'id':'p01','title':'Research page','claim':'Proposed mechanism','claim_status':'proposed',
            'source_ids':['notes'],'reference_ids':[],'text_runs':[{'id':'title','text':'Research page'}],
            'nodes':[{'id':'a'},{'id':'b'}], 'edges':[{'id':'ab','from':'a','to':'b','relation':'produces','arrow':'end'}],
            'formulas':[],'prompt':{'path':'prompt.md','status':'draft'},'image':None,'ppt_objects':[],'visual_review':None}]}
    def tearDown(self):self.temp.cleanup()
    def run_check(self,stage='content'):return check(self.project,self.root,stage)
    def test_content_and_prompt_drafts_valid(self):
        self.assertTrue(self.run_check()['passed']);self.assertTrue(self.run_check('prompts')['passed'])
    def test_dangling_arrow_rejected(self):
        self.project['pages'][0]['edges'][0]['to']='not-a-node'
        self.assertFalse(self.run_check()['passed'])
    def test_missing_source_rejected(self):
        self.project['pages'][0]['source_ids']=['invented']
        self.assertFalse(self.run_check()['passed'])
    def test_formula_without_definitions_rejected(self):
        self.project['pages'][0]['formulas']=[{'id':'f','canonical':'y=x'}]
        self.assertFalse(self.run_check()['passed'])
    def test_missing_prompt_rejected(self):
        self.project['pages'][0]['prompt']['path']='never-created.md'
        self.assertFalse(self.run_check('prompts')['passed'])
    def test_no_fake_image_completion(self):
        self.assertFalse(self.run_check('images')['passed'])
    def test_changed_source_hash_rejected(self):
        self.project['sources'][0]['sha256']='0'*64
        self.assertFalse(self.run_check()['passed'])
    def test_whole_reference_and_bitmap_declared_native_rejected(self):
        page=self.project['pages'][0]
        image=self.root/'reference.png';image.write_bytes(b'test-reference-byte-identity')
        page['image']={'path':'reference.png','sha256':digest(image),'origin':'provided','prompt_path':'prompt.md'}
        page['visual_review']={'scientific_checked':True,'ppt_render_checked':True}
        page['ppt_objects']=[{'id':'title','kind':'text','representation':'native_text','semantic_unit_count':1,'expected_text':'Research page'}]
        self.project['ppt']={'path':'fixture.pptx'}
        a='http://schemas.openxmlformats.org/drawingml/2006/main'
        p='http://schemas.openxmlformats.org/presentationml/2006/main'
        slide=f'<p:sld xmlns:p="{p}" xmlns:a="{a}"><p:cSld><p:spTree><p:pic><p:nvPicPr><p:cNvPr id="1" name="title"/></p:nvPicPr><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1600" cy="900"/></a:xfrm></p:spPr></p:pic></p:spTree></p:cSld></p:sld>'
        with zipfile.ZipFile(self.root/'fixture.pptx','w') as z:
            z.writestr('ppt/presentation.xml',f'<p:presentation xmlns:p="{p}"><p:sldSz cx="1600" cy="900"/></p:presentation>')
            z.writestr('ppt/slides/slide1.xml',slide)
            z.writestr('ppt/media/image1.png',image.read_bytes())
        result=self.run_check('ppt')
        self.assertFalse(result['passed'])
        self.assertTrue(any('Whole reference image embedded' in s for s in result['errors']))
        self.assertTrue(any('bitmap falsely declared native' in s for s in result['errors']))
        self.assertTrue(any('near-full-slide raster' in s for s in result['errors']))

if __name__=='__main__':unittest.main()
