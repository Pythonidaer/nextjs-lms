"""Generate a version-pinned LMS from the official vercel/next.js source (PyYAML)."""
import argparse,gzip,hashlib,json,pathlib,re,subprocess,yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
PIN='b0fad0d45eb4c4430fda5eeeb442e8a5af08a5f6'
def uid(s):return 'next-'+hashlib.sha256(s.encode()).hexdigest()[:16]
def route(p):return '/'.join(re.sub(r'^\d+-','',s) for s in p.with_suffix('').parts).removesuffix('/index')
def read(p):
 s=p.read_text();meta={}
 if s.startswith('---'):
  _,header,s=s.split('---',2);meta=yaml.safe_load(header) or {}
 return meta,s.strip()
TOKEN=re.compile(r'(?P<fence>`{3,})[^\n]*\n[\s\S]*?^(?P=fence)[ \t]*$|`[^`\n]+`|</?(?:AppOnly|PagesOnly)\s*>|\{/\*[\s\S]*?\*/\}',re.M)
def tokens(s):
 pos=0
 for m in TOKEN.finditer(s):
  if m.start()>pos:yield False,s[pos:m.start()]
  yield True,m.group();pos=m.end()
 if pos<len(s):yield False,s[pos:]
def clean(s,router,url):
 stack=[];out=[]
 for protected,x in tokens(s):
  if re.fullmatch(r'<(?:AppOnly|PagesOnly)\s*>',x):stack.append(x[1:-1].strip());continue
  if re.fullmatch(r'</(?:AppOnly|PagesOnly)\s*>',x):
   assert stack and stack.pop()==x[2:-1].strip(),url
   continue
  if router in ('app','pages') and any(t!=('AppOnly' if router=='app' else 'PagesOnly') for t in stack):continue
  if x.startswith('{/*'):continue
  if protected:out.append(x);continue
  def media(m):
   tag,props=m.groups();attrs=dict(re.findall(r'(src|alt|title)="([^"]*)"',props));target=attrs.get('src','')
   if target.startswith('/'):target='https://nextjs.org'+target
   label=attrs.get('alt') or attrs.get('title') or 'Official '+tag.lower()
   return '\n\n['+label+']('+target+')\n\n' if target else '\n\n'+label+' — see the linked source.\n\n'
  x=re.sub(r'<(Image|Video)\b([\s\S]*?)/>',media,x)
  x=re.sub(r'<Check\b[^>]*/>','Yes',x);x=re.sub(r'<Cross\b[^>]*/>','No',x)
  def card(m):
   text=m.group();title=re.search(r'title="([^"]*)"',text);href=re.search(r'href="([^"]*)"',text);snippets=re.findall(r"text: '((?:\\.|[^'])*)'",text)
   heading='['+title[1]+'](https://nextjs.org'+href[1]+')' if title and href else (title[1] if title else 'Suggested fix')
   return '\n\n'+heading+('\n\n```tsx\n'+'\n'.join(snippets)+'\n```' if snippets else '')+'\n\n'
  x=re.sub(r'<FixCard\b[\s\S]*?\n\s*/>',card,x);x=re.sub(r'</?FixCardGrid>','',x)
  x=re.sub(r'</?(?:details|summary|div|span)\b[^>]*>','',x)
  def link(m):
   label,target=m.groups()
   if target.startswith('/'):target='https://nextjs.org'+target
   elif target.startswith('#'):target=url+target
   return '['+label+']('+target+')'
  x=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',link,x);out.append(x)
 assert not stack,'Unclosed router scope '+url
 return ''.join(out).strip()
def split(s):
 chunks=[];heading='Overview';lines=[];fence=None
 for line in s.splitlines():
  m=re.match(r'^(`{3,}|~{3,})',line)
  if m:
   if fence is None:fence=m[1]
   elif line.strip()==fence:fence=None
  if fence is None and re.match(r'^#{1,3} ',line):
   if '\n'.join(lines).strip():chunks.append((heading,'\n'.join(lines).strip()))
   heading=re.sub(r'^#+ ','',line);lines=[]
  else:lines.append(line)
 if '\n'.join(lines).strip():chunks.append((heading,'\n'.join(lines).strip()))
 result=[]
 for title,text in chunks:
  if len(text)<19000:result.append((title,text));continue
  parts=[];buf=''
  for protected,atom in tokens(text):
   units=[atom] if protected else atom.split('\n\n')
   for unit in units:
    if len(unit)>18000 and not protected:
     if buf.strip():parts.append(buf.strip());buf=''
     header='\n'.join(unit.splitlines()[:2])+'\n' if unit.lstrip().startswith('|') else ''
     for line in unit.splitlines():
      if len(buf)+len(line)>12000:parts.append(buf.strip());buf=header
      buf+=line+'\n'
    else:
     if len(buf)+len(unit)>12000 and buf.strip():parts.append(buf.strip());buf=''
     buf+=unit+'\n\n'
  if buf.strip():parts.append(buf.strip())
  result.extend((title+f' ({i+1}/{len(parts)})',p) for i,p in enumerate(parts))
 return result
def deck(key,title,slides):return {'id':uid(key),'type':'slides','title':title,'slides':[{'id':uid(key+f'-slide-{i}'),'title':t,'body':b} for i,(t,b) in enumerate(slides)]}
def generate(source):
 revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
 assert revision==PIN,'Source checkout must be v16.3.8 at '+PIN
 docs=source/'docs';allpaths=sorted(docs.rglob('*.mdx'));paths=[p for p in allpaths if p.relative_to(docs).parts[0]!='02-pages'];lookup={route(p.relative_to(docs)):p for p in allpaths}
 excluded=[{'path':str(p.relative_to(source)),'reason':'Pages Router documentation'} for p in allpaths if p not in paths]
 pages_only_errors=set(json.loads((ROOT/'scripts/pages-only-errors.json').read_text()))
 errors=[p for p in sorted((source/'errors').glob('*.mdx')) if p.name not in pages_only_errors]
 excluded += [{'path':'errors/'+name,'reason':'Pages Router-specific troubleshooting'} for name in sorted(pages_only_errors)]
 def resolve(p,seen=None):
  seen=set() if seen is None else seen;assert p not in seen;seen.add(p);meta,body=read(p)
  if meta.get('source'):_,body,origin=resolve(lookup[meta['source']],seen)
  else:origin=p
  return meta,body,origin
 custom=json.loads((ROOT/'scripts/curriculum.json').read_text());sections=[{'id':uid('orientation-section'),'type':'section','title':'01 Start here — guided study path','children':[deck('orientation','Welcome and study strategy',custom['orientation'])]}]
 labels={'app/getting-started':'02 App Router — getting started','app/guides':'03 App Router — guides','app/api-reference':'04 App Router — API reference','app/glossary':'05 App Router — glossary','architecture':'06 Architecture','community':'07 Community','root':'08 Documentation overview','messages':'09 Troubleshooting — errors and warnings'}
 groups={};nested={};manifest=[]
 for p in paths+errors:
  error=p.parent==source/'errors';rel=pathlib.Path('messages')/p.name if error else p.relative_to(docs);r=route(rel);router=r.split('/')[0] if r.split('/')[0] in ('app','pages') else 'shared';url='https://nextjs.org/docs'+('' if r=='index' else '/'+r)
  if error:meta,body=read(p);origin=p
  else:meta,body,origin=resolve(p)
  title=str(meta.get('title') or p.stem.replace('-',' ').title());description=str(meta.get('description') or 'Understand '+title+' and its documented behavior.');prepared=clean(body,router,url);parts=split(prepared)
  slides=[('Learning goal and source',description+'\n\nRouter: '+router.title()+'. Version: 16.3.8.\n\nOfficial source: ['+title+']('+url+')\n\nUse the documented router, runtime and feature flags. Check experimental, deprecated and version-history notices before applying examples.')]+parts
  key='/'.join(r.split('/')[:2]) if router in ('app','pages') else r.split('/')[0]
  if key not in labels:key='root'
  if key not in groups:groups[key]={'id':uid('section-'+key),'type':'section','title':labels[key],'children':[]};sections.append(groups[key])
  target=groups[key];crumbs=r.split('/')[2:-1] if router in ('app','pages') else []
  for i,crumb in enumerate(crumbs):
   nk=key+'/'+('/'.join(crumbs[:i+1]))
   if nk not in nested:nested[nk]={'id':uid('group-'+nk),'type':'section','title':crumb.replace('-',' ').title(),'children':[]};target['children'].append(nested[nk])
   target=nested[nk]
  if key=='app/getting-started' and r.split('/')[-1] in custom['practice']:
   task,check=custom['practice'][r.split('/')[-1]];slides += [('Practice — build this locally',task),('Worked self-check',check+'\n\nExplain your decision and verify the result. Self-assessed, not automatically graded.')]
  related=meta.get('related') or {}
  if related.get('links'):slides.append(('Related documentation','\n'.join('- ['+x.split('/')[-1].replace('-',' ')+'](https://nextjs.org/docs/'+x+')' for x in related['links'])))
  node=deck('doc-'+r,title,slides);target['children'].append(node)
  manifest.append({'path':str(p.relative_to(source)),'sourcePath':str(origin.relative_to(source)),'url':url,'router':router,'lessonId':node['id'],'sourceSections':len(parts),'sourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'resolvedSHA256':hashlib.sha256(origin.read_bytes()).hexdigest()})
 sections.sort(key=lambda n:n['title']);sections.append({'id':uid('capstone-section'),'type':'section','title':'10 Capstone — build a learning dashboard','children':[deck('capstone','Build and review a Next.js learning dashboard',custom['capstone'])]})
 final=[]
 for key,bank in custom['quizzes'].items():
  qs=[]
  for i,(prompt,right,bad1,bad2,why) in enumerate(bank):
   answer=(len(final)+i)%3;options=[bad1,bad2];options.insert(answer,right);q={'id':uid(key+f'-q{i}'),'prompt':prompt,'options':options,'answer':answer,'explanation':why};qs.append(q);final.append(q)
  group=groups[key];group['children'].append({'id':uid(key+'-quiz'),'type':'quiz','title':'Knowledge check — '+group['title'][3:],'skill':group['title'][3:],'questions':qs})
 settings={'passScore':80,'allowRetakes':True,'showLessonDetails':False,'unlockAll':True,'sequential':False,'requireLessons':True,'brand':'#8da6ff','background':'#0c0e12','surface':'#14171d','text':'#edf0f7','muted':'#b4bac9','border':'#343b49','fontScale':1,'spacing':24,'contentWidth':1000,'radius':8,'font':'system','headingFont':'system','lineHeight':1.65}
 course={'schemaVersion':1,'id':'nextjs-16-3-8-documentation-course-v1','title':'Next.js App Router: From routing to production','description':'Official Next.js 16.3.8 App Router documentation, shared guides and relevant troubleshooting, with practice, quizzes and a capstone.','sections':sections,'settings':settings,'finalQuiz':{'id':uid('final'),'type':'quiz','title':'Final assessment — Next.js integration','skill':'Next.js integration','questions':[{**q,'id':uid('final-'+q['id'])} for q in final]}}
 canonical=json.dumps(course,indent=2,ensure_ascii=False)+'\n'
 (ROOT/'course.json').write_text(canonical)
 compressed=gzip.compress(canonical.encode(),mtime=0)
 (ROOT/'course.json.gz').write_bytes(compressed)
 scripts=['vendor/marked.umd.js','lesson-markdown.js','lms-runtime.js']
 (ROOT/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Next.js 16.3.8 App Router documentation, practice and progress reports."><title>Next.js App Router: From routing to production</title><link rel="stylesheet" href="lms.css">'+''.join('<script src="'+name+'" defer></script>' for name in scripts)+'</head><body class="lms-export-body"><div id="lms-root" role="status">Loading course…</div><noscript>This course needs JavaScript. Official docs: https://nextjs.org/docs</noscript></body></html>\n')
 (ROOT/'source-manifest.json').write_text(json.dumps({'version':'16.3.8','revision':revision,'retrieved':'2026-10-06','scope':'App Router documentation, shared architecture/community/overview and relevant troubleshooting from the pinned release. Pages Router pages and Pages-specific errors are excluded. App documentation may include brief comparisons or migration guidance. Separate /learn tutorials, blogs and historical releases are excluded.','excludedSources':excluded,'sources':manifest},indent=2)+'\n')
 (ROOT/'THIRD_PARTY_NOTICES.md').write_text('# Next.js documentation attribution\n\nAdapted from https://github.com/vercel/next.js/tree/v16.3.8/docs and /errors at commit '+revision+'. Source text and examples belong to Vercel and Next.js contributors. Shared pages are resolved, router-specific content selected, visual components linked and text split into slides. LMS objectives, practice, quizzes and capstone are authored additions.\n\n'+(source/'license.md').read_text())
 print('Source pages:',len(manifest),'source sections:',sum(m['sourceSections'] for m in manifest),'quiz questions:',len(final))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=pathlib.Path,required=True);generate(p.parse_args().source.resolve())
