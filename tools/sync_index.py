#!/usr/bin/env python3
import io, json, os, re, sys, urllib.request, urllib.parse, zipfile
from pathlib import Path
from datetime import datetime, timezone

SOURCE_REPO=os.environ.get("SOURCE_REPO","FAFF0x/gen2recomp")
GENERATION=os.environ.get("GENERATION","gen2")
ROOT=Path(__file__).parents[1]
OUT=ROOT/"site"/"data"
OUT.mkdir(parents=True,exist_ok=True)

UA={"User-Agent":"DuskPromised-GenRecomp-Index","Accept":"application/vnd.github+json"}
TOKEN=os.environ.get("GITHUB_TOKEN")
if TOKEN: UA["Authorization"]=f"Bearer {TOKEN}"

SOFT={
 "advanced_box_system_gen2":["gen2_modern_ui"],
 "free_evolution_shop_gen2":["all_tm_shop_gen2","gen2_modern_ui"],
 "pokemonmod_gen2_pokedex_plus":["gen2_modern_ui"],
 "pokemonmod_gen2_quest_system":["gen2_modern_ui"],
 "rocket_gym_ambushes_gen2":["pokemonmod_gen2_quest_system"],
}
EXTERNAL={
 "CRYSTAL_251":{
   "id":"CRYSTAL_251","title":"Crystal 251","author":"Deftones565","version":"0.11.6",
   "categories":["OPTIONAL","CONTENT"],"repo":"https://github.com/Deftones565/gen1recomp-mod-crystal-251",
   "downloadURL":"https://github.com/Deftones565/gen1recomp-mod-crystal-251/releases/download/v0.11.6/CRYSTAL_251-0.11.6.zip",
   "source_zip":"CRYSTAL_251-0.11.6.zip","summary":"Optional expanded-species integration referenced by FAFF0x manifests."
 },
 "BATTLE_ART_VOXEL_GEN2":{
   "id":"BATTLE_ART_VOXEL_GEN2","title":"Battle Art Voxel Gen 2","author":"absol89","version":"2.0.9",
   "categories":["DEPENDENCY","ART","UI"],"repo":"https://github.com/absol89/Gen2Recomped-DramaticShapes",
   "downloadURL":"https://github.com/absol89/Gen2Recomped-DramaticShapes/releases/download/2.0.9/BATTLE_ART_VOXEL_GEN2-2.0.9.zip",
   "source_zip":"BATTLE_ART_VOXEL_GEN2-2.0.9.zip","summary":"Compatible Battle Art Voxel Gen 2 dependency for FAFF0x's Voxel Performance Fix."
 },
}

def get(url,binary=False):
 req=urllib.request.Request(url,headers=UA)
 with urllib.request.urlopen(req,timeout=120) as r:
  data=r.read()
 return data if binary else data.decode("utf-8")

def get_json(url): return json.loads(get(url))
def dep_id(spec): return str(spec).split("@",1)[0]
def cats(m):
 c=m.get("categories") or m.get("category") or ["OTHER"]
 if isinstance(c,str): c=[c]
 c=[str(x).upper() for x in c]
 if "QUEST" in c and "CONTENT" not in c: c.insert(0,"CONTENT")
 return c
def authors(m):
 a=m.get("authors")
 if isinstance(a,list) and a: return str(a[0])
 if isinstance(a,str) and a: return a
 return "FAFF0x"
def version_key(v):
 return tuple(int(x) for x in re.findall(r"\d+",str(v))[:4])

owner,name=SOURCE_REPO.split("/",1)
branch=get_json(f"https://api.github.com/repos/{SOURCE_REPO}/branches/main")
commit=branch["commit"]["sha"]
tree=get_json(f"https://api.github.com/repos/{SOURCE_REPO}/git/trees/{commit}?recursive=1")
zips=sorted(x["path"] for x in tree.get("tree",[]) if x.get("type")=="blob" and x["path"].lower().endswith(".zip"))

mods={}
fail=[]
for path in zips:
 url=f"https://raw.githubusercontent.com/{SOURCE_REPO}/main/{urllib.parse.quote(path)}"
 try:
  blob=get(url,binary=True)
  with zipfile.ZipFile(io.BytesIO(blob)) as z:
   manifests=[n for n in z.namelist() if n.lower().endswith("manifest.json")]
   if not manifests: raise RuntimeError("manifest.json missing")
   manifest_name=sorted(manifests,key=lambda s:(s.count("/"),len(s)))[0]
   m=json.loads(z.read(manifest_name).decode("utf-8"))
 except Exception as e:
  fail.append(f"{path}: {e}")
  continue
 mid=m.get("id") or re.sub(r"_v\d.*$","",Path(path).stem)
 entry={
   "folder":f"{authors(m).replace(' ','')}@{mid}",
   "id":mid,"title":m.get("name") or m.get("title") or mid,
   "author":authors(m),"version":str(m.get("version") or "0.0.0"),
   "categories":cats(m),"summary":m.get("description") or "",
   "tags":m.get("tags") or [],"api":m.get("api",2),"profile":m.get("profile","content"),
   "permissions":m.get("permissions") or [],"dependencies":m.get("dependencies") or [],
   "optional_dependencies":m.get("optional_dependencies") or [],
   "optional_integrations":SOFT.get(mid,[]),"conflicts":m.get("conflicts") or [],
   "affects_link":bool(m.get("affects_link",False)),"experimental":bool(m.get("experimental",False)),
   "repo":f"https://github.com/{SOURCE_REPO}","downloadURL":url,"source_zip":Path(path).name,
   "source_scope":SOURCE_REPO,"update_check":"off"
 }
 if m.get("game_version"): entry["game_version"]=m["game_version"]
 old=mods.get(mid)
 if not old:
  mods[mid]=entry
 elif "android" in Path(path).name.lower():
  old.setdefault("alternate_downloads",[]).append({"label":"Android edition","name":Path(path).name,"url":url})
 elif "android" in old.get("source_zip","").lower():
  entry.setdefault("alternate_downloads",[]).append({"label":"Android edition","name":old["source_zip"],"url":old["downloadURL"]})
  mods[mid]=entry
 elif version_key(entry["version"])>version_key(old["version"]):
  entry.setdefault("alternate_downloads",[]).append({"label":"Alternate build","name":old["source_zip"],"url":old["downloadURL"]})
  mods[mid]=entry
 else:
  old.setdefault("alternate_downloads",[]).append({"label":"Alternate build","name":Path(path).name,"url":url})

source_ids=set(mods)
hard={dep_id(x) for m in mods.values() for x in m["dependencies"]}-source_ids
opt={dep_id(x) for m in mods.values() for x in m["optional_dependencies"]}-source_ids
canonical={}
try:
 c=get_json("https://raw.githubusercontent.com/bryanthaboi/gen1recomp-mod-index/main/site/data/index.json")
 canonical={m.get("id"):m for m in c.get("mods",[]) if m.get("id")}
except Exception: pass

for did in sorted(hard|opt):
 if did in EXTERNAL:
  x=dict(EXTERNAL[did])
 elif did in canonical:
  c=canonical[did]; latest=c.get("latest") or {}; z=(latest.get("zip") or {})
  x={
   "id":did,"title":c.get("title") or did,"author":c.get("author") or "Unknown",
   "version":str(latest.get("version") or c.get("version") or "0.0.0"),
   "categories":c.get("categories") or ["DEPENDENCY"],"repo":c.get("repo"),
   "downloadURL":z.get("url") or c.get("downloadURL"),
   "source_zip":z.get("name") or "release asset","summary":c.get("summary") or "",
   "permissions":c.get("permissions") or [],"dependencies":c.get("dependencies") or [],
   "optional_dependencies":c.get("optional_dependencies") or [],"conflicts":c.get("conflicts") or [],
   "profile":c.get("profile","content"),"api":c.get("api",2)
  }
 else:
  fail.append(f"Unresolved external dependency: {did}")
  continue
 if not x.get("downloadURL"):
  fail.append(f"External dependency has no download URL: {did}"); continue
 x.setdefault("folder",f"{str(x.get('author','External')).replace(' ','')}@{did}")
 x.setdefault("permissions",[]); x.setdefault("dependencies",[]); x.setdefault("optional_dependencies",[])
 x.setdefault("optional_integrations",[]); x.setdefault("conflicts",[]); x.setdefault("profile","content"); x.setdefault("api",2)
 x.setdefault("affects_link",False); x.setdefault("experimental",False); x["update_check"]="off"
 x["source_scope"]="Required external dependency" if did in hard else "Optional external integration"
 mods[did]=x

if fail:
 print("\n".join("ERROR: "+x for x in fail),file=sys.stderr)
 sys.exit(1)

entries=sorted(mods.values(),key=lambda m:m["title"].lower())
ids=[m["id"] for m in entries]
if len(ids)!=len(set(ids)): raise SystemExit("duplicate IDs")

feed={
 "schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),
 "categories":sorted({c for m in entries for c in m.get("categories",[])}),
 "base_games":["red","blue","yellow"] if GENERATION=="gen1" else ["gold","silver","crystal"],
 "mods":entries,"carts":[],
 "index_notes":{
  "relationship_fields":{
   "dependencies":"Hard manifest dependencies. Required.",
   "optional_dependencies":"Dependencies explicitly declared optional by the mod manifest.",
   "optional_integrations":"Documented soft/coexistence integrations. Not required.",
   "conflicts":"Documented conflicts."
  },
  "download_policy":"Author-hosted downloads only. No ROMs or mirrored mod ZIP binaries."
 }
}
(OUT/"index.json").write_text(json.dumps(feed,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
prov={"generated_at":feed["generated_at"],"source_repository":f"https://github.com/{SOURCE_REPO}","source_commit":commit,
      "source_zip_count":len(zips),"entry_count":len(entries),
      "policy":"No ROMs or mirrored mod binaries are stored in this repository."}
(OUT/"provenance.json").write_text(json.dumps(prov,indent=2)+"\n",encoding="utf-8")
(ROOT/"VALIDATION.md").write_text(
 f"# Validation report\n\nSource: {SOURCE_REPO}\n\nCommit: `{commit}`\n\nZIPs inspected: **{len(zips)}**\n\nFeed entries: **{len(entries)}**\n\nAll source ZIPs were downloaded successfully and their manifests parsed.\n",
 encoding="utf-8")
print(f"OK: {SOURCE_REPO} @ {commit}: {len(zips)} ZIPs -> {len(entries)} feed entries")
