// Preserve licenses for all production dependencies in the static distribution.
import fs from 'node:fs';
import path from 'node:path';
const lock=JSON.parse(fs.readFileSync('package-lock.json','utf8'));
let text='# Third-party software notices\n\nGenerated from pinned production dependencies. Original texts follow; package names and versions identify the distributed components.\n';
for(const [dir,entry] of Object.entries(lock.packages)){
  if(!dir||entry.dev)continue;
  const meta=JSON.parse(fs.readFileSync(path.join(dir,'package.json'),'utf8'));
  const names=fs.readdirSync(dir).filter(n=>/^(licen[cs]e|copying|notice|ofl)(\.|$|-)/i.test(n)&&fs.statSync(path.join(dir,n)).isFile());
  text+=`\n## ${meta.name} ${meta.version}\n\nDeclared license: ${meta.license??entry.license??'See package'}\n`;
  for(const name of names)text+=`\n### ${name}\n\n\`\`\`text\n${fs.readFileSync(path.join(dir,name),'utf8')}\n\`\`\`\n`;
  if(!names.length&&fs.existsSync(path.join(dir,'README.md'))){const readme=fs.readFileSync(path.join(dir,'README.md'),'utf8');const start=readme.search(/^## License/m);if(start>=0)text+=`\n${readme.slice(start)}\n`;}
  if(!names.length)text+=`\nPackage source: https://www.npmjs.com/package/${meta.name}/v/${meta.version}\n`;
}
fs.mkdirSync('public/notices',{recursive:true});
fs.writeFileSync('public/notices/software.md',text);
