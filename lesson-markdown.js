/* Render documentation Markdown, preserving examples without executing source HTML. */
window.LMSMarkdown = function (text) {
  const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const renderer=new marked.Renderer();
  renderer.html=({text})=>escape(text);
  renderer.code=({text,lang})=>{const filename=(lang||'').match(/filename="([^"]*)"/),pkg=(lang||'').match(/package="([^"]*)"/);const caption=[filename?.[1],pkg?'Package manager: '+pkg[1]:''].filter(Boolean).join(' · ');return (caption?'<p><strong>'+escape(caption)+'</strong></p>':'')+'<pre><code>'+escape(text)+'</code></pre>';};
  const template=document.createElement('template');
  template.innerHTML=marked.parse(String(text),{renderer,gfm:true});
  const allowed=new Set(['P','BR','STRONG','EM','DEL','CODE','PRE','BLOCKQUOTE','UL','OL','LI','H1','H2','H3','H4','H5','H6','HR','TABLE','THEAD','TBODY','TR','TH','TD','A','IMG']);
  for(const node of [...template.content.querySelectorAll('*')]){
    if(!allowed.has(node.tagName)){node.replaceWith(document.createTextNode(node.textContent));continue;}
    const href=node.getAttribute('href'),src=node.getAttribute('src'),alt=node.getAttribute('alt');
    for(const attr of [...node.attributes])node.removeAttribute(attr.name);
    if(node.tagName==='A'&&href){try{const url=new URL(href,location.href);if(['https:','http:'].includes(url.protocol)){node.href=url.href;node.target='_blank';node.rel='noopener noreferrer';}}catch{}}
    if(node.tagName==='IMG'){try{const url=new URL(src,location.href);if(url.protocol==='https:'){node.src=url.href;node.alt=alt||'Documentation diagram';node.loading='lazy';}else node.replaceWith(document.createTextNode(alt||'Diagram'));}catch{node.replaceWith(document.createTextNode(alt||'Diagram'));}}
  }
  return template.innerHTML;
};
