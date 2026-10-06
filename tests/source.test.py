import hashlib,importlib.util,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'scripts/build_course.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
class BuilderTests(unittest.TestCase):
 def test_router_selection_preserves_examples(self):
  text='<AppOnly>App text</AppOnly>\n<PagesOnly>Pages text</PagesOnly >\n```tsx filename="example.tsx"\nimport X from "x"\n// <PagesOnly>literal</PagesOnly>\n# Not a heading\n```\nInline `<Image />`.'
  app=builder.clean(text,'app','https://nextjs.org/docs/app/example');pages=builder.clean(text,'pages','https://nextjs.org/docs/pages/example')
  self.assertIn('App text',app);self.assertNotIn('Pages text',app);self.assertIn('Pages text',pages);self.assertNotIn('App text',pages)
  self.assertIn('import X from "x"',app);self.assertIn('// <PagesOnly>literal</PagesOnly>',app);self.assertIn('Inline `<Image />`.',app)
  self.assertEqual(len(builder.split(app)),1)
 def test_relative_links(self):
  text='[one](/docs/app/test) [two](#heading) `literal [three](/docs/keep)`'
  out=builder.clean(text,'app','https://nextjs.org/docs/app/example')
  self.assertIn('(https://nextjs.org/docs/app/test)',out);self.assertIn('(https://nextjs.org/docs/app/example#heading)',out);self.assertIn('`literal [three](/docs/keep)`',out)
 def test_complete_source_coverage(self):
  source=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
  if not source:self.skipTest('Pass source checkout path to verify upstream coverage')
  manifest=json.loads((ROOT/'source-manifest.json').read_text());expected={str(p.relative_to(source)) for p in (source/'docs').rglob('*.mdx')}|{str(p.relative_to(source)) for p in (source/'errors').glob('*.mdx')}
  included={m['path'] for m in manifest['sources']};excluded={m['path'] for m in manifest['excludedSources']};self.assertEqual(expected,included|excluded);self.assertFalse(included&excluded);self.assertFalse(any(p.startswith('docs/02-pages/') for p in included))
  for m in manifest['sources']:
   self.assertEqual(hashlib.sha256((source/m['path']).read_bytes()).hexdigest(),m['sourceSHA256']);self.assertEqual(hashlib.sha256((source/m['sourcePath']).read_bytes()).hexdigest(),m['resolvedSHA256'])
if __name__=='__main__':unittest.main(argv=[sys.argv[0]])
