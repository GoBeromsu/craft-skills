#!/usr/bin/env python3
"""Offline, read-only DESIGN.md and evidence-manifest checker (schema v1)."""
import argparse, datetime as dt, hashlib, html.parser, json, re, sys, unicodedata
from pathlib import Path

H2 = ["Product Intent", "Principles", "Tokens", "Typography", "Layout and Responsive", "Primitives", "Interaction and Feedback", "Motion", "Accessibility", "Verification", "Accepted Debt"]
DOC_LIMIT = "Reports document structure/declaration only; it does not establish rendered behavior or conformance."
INSUFF = "No defect or pass conclusion may be drawn; obtain named evidence or perform a manual/rendered audit."
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ROLES = {"button","link","checkbox","radio","switch","textbox","combobox","listbox","menuitem","tab","slider","spinbutton"}
CHECKS = {"UX_SRC_ICON_CONTROL_NAME_MISSING":"source", "UX_SRC_REDUCED_MOTION_MISSING":"source", "UX_RENDER_CONTROL_NAME_MISSING":"render", "UX_RENDER_FOCUS_EVIDENCE_MISSING":"render"}

def norm(s, collapse=True):
    s = unicodedata.normalize("NFC", str(s)).strip()
    return re.sub(r"[ \t\r\n\f\v]+", " ", s) if collapse else s

def key(s): return norm(s).casefold()
def substantive(s):
    value=norm(s)
    placeholder=r"(?:<[^<>]*>|\{[^{}]*\})"
    template_key=rf"(?:[A-Za-z0-9_.-]|{placeholder})+:\s*{placeholder}"
    return (
        value.casefold() not in {"", "...", "tbd", "todo", "-"}
        and not re.fullmatch(placeholder, value)
        and not re.fullmatch(template_key, value)
    )
def location(line): return f"line {line}" if line else ""

class Result:
    def __init__(self): self.diags=[]; self.performed=[]; self.coverage={}; self.invalid=False
    def add(self, code, level, domain, path="", loc="", observed="", limitation=DOC_LIMIT, evidence_id=None):
        d={"code":code,"level":level,"evidence_kind":domain,"path":path,"location":loc,"observed":observed,"limitation":limitation}
        if evidence_id is not None: d["evidence_id"]=evidence_id
        self.diags.append(d)
    def check(self, code, domain, status): self.performed.append({"code":code,"domain":domain,"status":status})

def clean_lines(text):
    out=[]; fence=False; comment=False
    for n, raw in enumerate(text.splitlines(), 1):
        line=raw
        if re.match(r"^\s*(```|~~~)", line): fence=not fence; out.append((n,"")); continue
        if fence: out.append((n,"")); continue
        while "<!--" in line:
            a,b=line.split("<!--",1); comment=True
            if "-->" in b: line=a+b.split("-->",1)[1]; comment=False
            else: line=a; break
        if comment:
            if "-->" in line: line=line.split("-->",1)[1]; comment=False
            else: line=""
        out.append((n,line))
    return out

def fields(lines):
    found={}; dup=[]
    for no,line in lines:
        m=re.match(r"^- ([a-z_]+):\s*(.*?)\s*$",line)
        if m:
            k,v=m.groups()
            if k in found: dup.append((k,no))
            else: found[k]=(v,no)
    return found,dup

def table(lines):
    rows=[]
    for no,line in lines:
        if "|" in line and line.strip().startswith("|"):
            cells=[norm(x) for x in line.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", x) for x in cells): rows.append((no,cells))
    return rows

def document(root,r):
    cur=root/"DESIGN.md"; legacy=root/"docs/design.md"; path="DESIGN.md"
    if not cur.exists() and legacy.exists(): r.add("DESIGN_PATH_LEGACY","error","filesystem",str(legacy.relative_to(root)),"", "Only legacy docs/design.md exists"); r.check("DESIGN_PATH_LEGACY","filesystem","violation"); return
    if not cur.exists(): r.add("DESIGN_PATH_MISSING","error","filesystem",path,"","DESIGN.md is missing"); r.check("DESIGN_PATH_MISSING","filesystem","violation"); return
    if legacy.exists(): r.add("DESIGN_PATH_CONFLICT","error","filesystem",path,"","Both DESIGN.md and docs/design.md exist")
    text=cur.read_text(encoding="utf-8"); lines=clean_lines(text); hs=[]; all_h2=[]
    for i,(no,line) in enumerate(lines):
        m=re.match(r"^ {0,3}## (.+?)\s*$",line)
        if m:
            name=norm(re.sub(r"\s+#+\s*$","",m.group(1))); k=key(name)
            all_h2.append((name,no,i))
            if k in {key(x) for x in H2}: hs.append((H2[[key(x) for x in H2].index(k)],no,i))
    by={}
    for h in hs: by.setdefault(h[0],[]).append(h)
    for h in H2:
        if h not in by: r.add("DESIGN_SECTION_MISSING","error","document",path,"","Missing "+h)
        elif len(by[h])>1: r.add("DESIGN_SECTION_DUPLICATE","error","document",path,location(by[h][1][1]),"Duplicate "+h)
    order=[H2.index(x[0]) for x in hs]
    if order != sorted(order): r.add("DESIGN_SECTION_ORDER","error","document",path,"","Canonical H2 headings are out of order")
    for h,_,idx in hs:
        end=next((x[2] for x in all_h2 if x[2]>idx),len(lines)); body=lines[idx+1:end]
        meaningful=[]
        for _,line in body:
            stripped=line.strip()
            if not stripped or stripped.startswith(("|",">")) or re.match(r"^ {0,3}#{1,6}\s+",line):
                continue
            field_match=re.match(r"^- ([a-z_]+):\s*(.*?)\s*$",line)
            candidate=field_match.group(2) if field_match else re.sub(r"^[-*+]\s+","",stripped)
            if substantive(candidate):
                meaningful.append(line)
        rows=table(body)
        if not meaningful and len(rows)<2:
            r.add("DESIGN_SECTION_EMPTY","error","document",path,location(lines[idx][0]),h)
    # Motion
    if "Motion" in by:
        idx=by["Motion"][0][2]; end=next((x[2] for x in all_h2 if x[2]>idx),len(lines)); f,d=fields(lines[idx+1:end])
        for k,n in d:r.add("DESIGN_FIELD_DUPLICATE","error","document",path,location(n),k)
        for k,(_,no) in f.items():
            if k not in {"motion_present","reduced_motion"}: r.add("DESIGN_FIELD_INVALID","error","document",path,location(no),k)
        mp=f.get("motion_present"); rm=f.get("reduced_motion")
        if not mp or mp[0] not in {"true","false"}: r.add("DESIGN_FIELD_INVALID","error","document",path,location((mp or ("",0))[1]),"motion_present")
        elif mp[0]=="true" and (not rm or not substantive(rm[0]) or key(rm[0]) in {"none","not_applicable"}): r.add("UX_DOC_REDUCED_MOTION_MISSING","error","document",path,location((rm or mp)[1]),"reduced_motion")
        elif mp[0]=="false" and (not rm or key(rm[0])!="not_applicable"): r.add("DESIGN_FIELD_INVALID","error","document",path,location((rm or mp)[1]),"reduced_motion")
    # primitives
    if "Primitives" in by:
        idx=by["Primitives"][0][2]; end=next((x[2] for x in all_h2 if x[2]>idx),len(lines)); b=lines[idx+1:end]; starts=[]
        for j,(no,line) in enumerate(b):
            m=re.match(r"^ {0,3}### (.+?)\s*$",line)
            if m: starts.append((key(m.group(1)),no,j))
        seen=set()
        for pid,no,j in starts:
            if not pid or pid in seen:r.add("DESIGN_PRIMITIVE_DUPLICATE","error","document",path,location(no),pid)
            seen.add(pid); e=next((x[2] for x in starts if x[2]>j),len(b)); part=b[j+1:e]; f,d=fields(part)
            for k,n in d:r.add("DESIGN_FIELD_DUPLICATE","error","document",path,location(n),k)
            for k,(_,field_no) in f.items():
                if k!="data_bearing": r.add("DESIGN_FIELD_INVALID","error","document",path,location(field_no),k)
            db=f.get("data_bearing")
            if not db or db[0] not in {"true","false"}: r.add("DESIGN_FIELD_INVALID","error","document",path,location(no),"data_bearing") ; continue
            ts=table(part)
            if not ts or [key(x) for x in ts[0][1]] != ["state","specification","same_as","non_color_cue"]: r.add("DESIGN_TABLE_INVALID","error","document",path,location(no),"primitive state table"); continue
            states={}; refs=[]
            for rn,row in ts[1:]:
                if len(row)!=4: r.add("DESIGN_TABLE_INVALID","error","document",path,location(rn),"row"); continue
                st=key(row[0])
                if st in states:r.add("DESIGN_STATE_DUPLICATE","error","document",path,location(rn),row[0])
                states[st]=(row,rn); refs.append((st,row[2],row[1],rn))
                cue=key(row[3])
                if cue=="none":r.add("UX_DOC_NON_COLOR_CUE_NONE","error","document",path,location(rn),"non_color_cue: none")
                elif cue not in {"not_applicable"} and not substantive(row[3]):r.add("DESIGN_FIELD_INVALID","error","document",path,location(rn),"non_color_cue")
            required={"default","hover","active","focus","disabled","loading"}|({"empty","error"} if db[0]=="true" else set())
            for st in sorted(required-set(states)):r.add("DESIGN_STATE_MISSING","error","document",path,location(no),st)
            for st,ref,spec,rn in refs:
                if ref!="-":
                    if not substantive(ref) or key(ref)==st or key(ref) not in states or spec!="-":r.add("DESIGN_STATE_REFERENCE_INVALID","error","document",path,location(rn),st)
                elif not substantive(spec):r.add("DESIGN_FIELD_INVALID","error","document",path,location(rn),"specification")
            # same_as is a directed graph; every cycle is invalid, not merely self links.
            graph={st:key(ref) for st,ref,_,_ in refs if ref!="-"}
            for start in graph:
                seen=set(); current=start
                while current in graph:
                    if current in seen:
                        r.add("DESIGN_STATE_REFERENCE_INVALID","error","document",path,location(states[start][1]),start); break
                    seen.add(current); current=graph[current]
    # debt
    if "Accepted Debt" in by:
        idx=by["Accepted Debt"][0][2]; end=next((x[2] for x in all_h2 if x[2]>idx),len(lines)); ts=table(lines[idx+1:end])
        if not ts or [key(x) for x in ts[0][1]] != ["id","decision","date","upgrade_path"]: r.add("DESIGN_TABLE_INVALID","error","document",path,"","accepted debt table")
        else:
            debt_ids=set()
            for no,row in ts[1:]:
                if len(row)!=4:
                    r.add("DESIGN_TABLE_INVALID","error","document",path,location(no),"accepted debt row")
                    continue
                did=key(row[0])
                if not substantive(row[0]) or did in debt_ids: r.add("DESIGN_FIELD_INVALID","error","document",path,location(no),"debt id")
                debt_ids.add(did)
                if not substantive(row[1]): r.add("DESIGN_FIELD_INVALID","error","document",path,location(no),"decision")
                try: dt.date.fromisoformat(row[2])
                except ValueError:r.add("DESIGN_DEBT_DATE_MISSING","error","document",path,location(no),row[2])
                if not substantive(row[3]):r.add("DESIGN_DEBT_UPGRADE_MISSING","error","document",path,location(no),row[3])
    r.check("DESIGN_DOCUMENT","document","violation" if any(d["evidence_kind"] in {"document","filesystem"} and d["level"]=="error" for d in r.diags) else "passed")

def invalid(r,msg): r.invalid=True; r.add("EVIDENCE_MANIFEST_INVALID","error","evidence","","",msg,"Manifest schema/integrity error.")
class IconParser(html.parser.HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True); self.roots=[]; self.stack=[]; self.ambiguous=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if len(a)!=len(attrs): self.ambiguous=True
        node={"tag":tag,"attrs":a,"children":[],"line":self.getpos()[0]}
        if self.stack: self.stack[-1]["children"].append(node)
        else: self.roots.append(node)
        if tag not in self.VOID_TAGS:
            self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS:
            self.handle_endtag(tag)
    def handle_data(self, data):
        if self.stack: self.stack[-1]["children"].append(data)
    def handle_endtag(self, tag):
        if not self.stack: self.ambiguous=True; return
        item=self.stack.pop()
        if item["tag"] != tag: self.ambiguous=True

def descendants(node):
    for child in node["children"]:
        if isinstance(child,dict):
            yield child
            yield from descendants(child)

def node_text(node, inside_svg=False):
    if key(node["attrs"].get("aria-hidden") or "")=="true": return ""
    inside_svg=inside_svg or node["tag"]=="svg"
    result=[]
    for child in node["children"]:
        if isinstance(child,str): result.append(child)
        elif child["tag"] in {"script","style","template"}: continue
        elif child["tag"]=="title" and not inside_svg: continue
        else: result.append(node_text(child,inside_svg))
    return norm(" ".join(result))

def dynamic_markup(value):
    return bool(re.search(r"\{\{|\{%|\$\{|<%|(?<!\{)\{(?!\{)",str(value)))

def node_has_dynamic(node):
    if any(dynamic_markup(value) for _,value in node["attrs"].items() if value is not None):
        return True
    for child in node["children"]:
        if isinstance(child,str):
            if dynamic_markup(child):
                return True
        elif node_has_dynamic(child):
            return True
    return False

def css_mask(source):
    """Mask comments/strings while retaining structural punctuation and offsets."""
    out=list(source); i=0
    while i<len(source):
        if source.startswith("/*",i):
            end=source.find("*/",i+2)
            if end<0: return None
            for j in range(i,end+2): out[j]=" "
            i=end+2; continue
        if source[i] in "'\"":
            quote=source[i]; j=i+1
            while j<len(source) and source[j]!=quote:
                j += 2 if source[j]=="\\" else 1
            if j>=len(source): return None
            for k in range(i,j+1): out[k]=" "
            i=j+1; continue
        i+=1
    return "".join(out)

def balanced_blocks(masked):
    stack=[]; blocks=[]
    for i,char in enumerate(masked):
        if char=="{": stack.append(i)
        elif char=="}":
            if not stack: return None
            blocks.append((stack.pop(),i))
    return blocks if not stack else None

def source_observations(root, sources, code, r):
    """Bounded literal HTML/CSS observations; unsupported syntax is insufficiency."""
    selected=[s for s in sources if (code.endswith("ICON_CONTROL_NAME_MISSING") and s["kind"]=="html") or (code.endswith("REDUCED_MOTION_MISSING") and s["kind"]=="css")]
    if not selected:
        r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"No supported enumerated source",INSUFF); return False
    if code == "UX_SRC_ICON_CONTROL_NAME_MISSING":
        ambiguous=False
        for s in selected:
            raw=(root/s["path"]).read_text(encoding="utf-8")
            p=IconParser()
            try: p.feed(raw); p.close()
            except Exception: ambiguous=True; continue
            ambiguous |= p.ambiguous or bool(p.stack)
            ids={}; duplicate_ids=set()
            for node in [*p.roots, *(x for root_node in p.roots for x in descendants(root_node))]:
                ident=node["attrs"].get("id")
                if ident:
                    if ident in ids: duplicate_ids.add(ident)
                    else: ids[ident]=node

            def resolve_labelled(ref, trail):
                if ref in trail or ref not in ids or ref in duplicate_ids:
                    return None
                target=ids[ref]
                nested=target["attrs"].get("aria-labelledby")
                if not nested:
                    return node_text(target)
                refs=nested.split()
                if not refs or len(set(refs)) != len(refs):
                    return None
                values=[resolve_labelled(item, trail | {ref}) for item in refs]
                if any(value is None for value in values):
                    return None
                return norm(" ".join(values))

            for node in [*p.roots, *(x for root_node in p.roots for x in descendants(root_node))]:
                tag,a,line=node["tag"],node["attrs"],node["line"]
                if tag=="a":
                    href=a.get("href")
                    if href is None or not norm(href): continue
                    if dynamic_markup(href):
                        ambiguous=True
                        continue
                elif tag!="button":
                    continue
                if "hidden" in a or key(a.get("aria-hidden") or "")=="true": continue
                if node_has_dynamic(node) or (a.get("id") and a["id"] in duplicate_ids):
                    ambiguous=True
                    continue
                label=a.get("aria-label","")
                if label and substantive(label): continue
                candidate_ambiguous=False
                labelled=a.get("aria-labelledby")
                if labelled:
                    refs=labelled.split()
                    if not refs or any(x not in ids for x in refs) or len(set(refs)) != len(refs) or a.get("id") in refs:
                        candidate_ambiguous=True
                    else:
                        labels=[resolve_labelled(item, {a.get("id")} if a.get("id") else set()) for item in refs]
                        if any(item is None for item in labels): candidate_ambiguous=True
                        elif norm(" ".join(labels)): continue
                allowed_descendants={"svg","path","use","i","span","img","title","script","style","template"}
                if any(child["tag"] not in allowed_descendants for child in descendants(node)):
                    candidate_ambiguous=True
                if candidate_ambiguous:
                    ambiguous=True
                    continue
                if node_text(node): continue
                for child in descendants(node):
                    ctag,ca=child["tag"],child["attrs"]
                    if key(ca.get("aria-hidden") or "")=="true": continue
                    if ctag == "img":
                        if dynamic_markup(ca.get("alt","")): candidate_ambiguous=True
                        elif substantive(ca.get("alt","")): candidate_ambiguous=False; break
                    elif ctag == "svg":
                        if any(x["tag"]=="title" and substantive(node_text(x)) for x in descendants(child)): candidate_ambiguous=False; break
                    elif ctag not in {"path","use","i","span","script","style","template"}: candidate_ambiguous=True
                else:
                    if candidate_ambiguous or p.ambiguous:
                        ambiguous=True; continue
                    # Literal, fully tokenized decorative-only candidate.
                    r.add(code,"error","source",s["path"],location(line),f"literal <{tag}> has no literal name evidence","Static source only; runtime DOM, CSS-hidden text, framework binding, shadow DOM, and computed accessibility name are unresolved.")
                    continue
                # A name-bearing image/title suppresses the candidate.
                continue
        if ambiguous: r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"Dynamic, malformed, or unresolved name syntax",INSUFF)
    else:
        corpus="\n".join((root/s["path"]).read_text(encoding="utf-8") for s in selected)
        stripped=css_mask(corpus)
        blocks=balanced_blocks(stripped) if stripped is not None else None
        if blocks is None or re.search(r"@import\b",stripped):
            r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"Unsupported CSS syntax or corpus ambiguity",INSUFF); return False
        if re.search(r"(?:^|[;{])\s*(?:--?[\w-]*(?:animation|transition)-duration)\s*:",stripped):
            r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"Custom or prefixed duration property",INSUFF); return False
        shorthand=bool(re.search(r"(?:^|[;{])\s*(?:animation|transition)\s*:",stripped))
        vals=re.findall(r"(?:^|[;{])\s*(?:animation-duration|transition-duration)\s*:\s*([^;}]+)",stripped)
        nonzero=False
        for val in vals:
            for v in val.split(","):
                v=v.strip()
                m=re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s)?",v)
                if not m or (m.group(2) is None and m.group(1)!="0"):
                    r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"Nonliteral duration",INSUFF); return False
                nonzero |= float(m.group(1)) > 0
        if shorthand and not nonzero:
            r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"Shorthand motion without independent nonzero longhand evidence",INSUFF); return False
        qualifying=False
        motion_media_ambiguity=False
        for opening,closing in blocks:
            prefix=stripped[max(0,stripped.rfind("}",0,opening)+1):opening]
            media=re.fullmatch(r"\s*@media\s+(.+?)\s*",prefix,re.S)
            if not media: continue
            condition=media.group(1).strip()
            exact_features=re.findall(r"\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)",condition,re.I)
            exact=len(exact_features)==1
            negated=bool(re.search(r"\bnot\b",condition,re.I))
            body=stripped[opening+1:closing]
            declaration=re.search(r"(?:^|[;{])\s*[A-Za-z][-\w]*\s*:\s*[^;{}]+;?",body)
            if exact and not negated and declaration:
                qualifying=True; break
            if "prefers-reduced-motion" in condition.casefold() and (
                not exact
                or negated
            ):
                motion_media_ambiguity=True
        if motion_media_ambiguity and not qualifying:
            r.add("UX_EVIDENCE_INSUFFICIENT","info","source","",code,"Nonqualifying reduced-motion media condition",INSUFF); return False
        if nonzero and not qualifying:
            r.add(code,"error","source","", "","Nonzero literal motion without qualifying reduced-motion block","Does not resolve imports/cascade/runtime styles/essential motion.")
    return any(d["code"]==code and d["level"]=="error" for d in r.diags)
def evidence(root,ep,r):
    try: data=json.loads(ep.read_text(encoding="utf-8"))
    except Exception as e: invalid(r,"Cannot parse evidence JSON: "+str(e)); return
    top={"schema_version","producer","checks","sources","accessibility_nodes","focus_expectations","captures","artifacts"}
    if not isinstance(data,dict) or set(data)!=top or data.get("schema_version")!=1: invalid(r,"Top-level schema_version or keys are invalid"); return
    p=data["producer"]
    if not isinstance(p,dict) or set(p)-{"name","version","run_id"} or not all(isinstance(p.get(k),str) and bool(norm(p[k])) for k in ("name","version")) or ("run_id" in p and (not isinstance(p["run_id"],str) or not norm(p["run_id"]))): invalid(r,"producer is invalid")
    for k in ("checks","sources","accessibility_nodes","focus_expectations","captures","artifacts"):
        if not isinstance(data[k],dict if k=="checks" else list):invalid(r,k+" has wrong type")
    if r.invalid:return
    ids=set(); nodes={}; locs=set(); artifacts={}
    def safe_path(v):
        if not isinstance(v,str) or not v or "\x00" in v or "\\" in v or Path(v).is_absolute() or ".." in Path(v).parts: return None
        q=(root/Path(*Path(v).parts)).resolve()
        try:q.relative_to(root.resolve())
        except ValueError:return None
        return q if q.is_file() else None
    for group in ("sources","accessibility_nodes","captures","artifacts"):
        for o in data[group]:
            if not isinstance(o,dict) or not ID.fullmatch(o.get("id", "")) or o["id"] in ids: invalid(r,"Duplicate or invalid ID in "+group); continue
            ids.add(o["id"])
            if group=="sources":
                if set(o)!={"id","kind","path"} or o["kind"] not in {"html","css"} or not safe_path(o["path"]) or (o["kind"]=="html" and Path(o["path"]).suffix.lower() not in {".html",".htm"}) or (o["kind"]=="css" and Path(o["path"]).suffix.lower()!=".css"):invalid(r,"Invalid source")
            elif group=="accessibility_nodes":
                if set(o)!={"id","role","name","locator"} or not isinstance(o["role"],str) or not isinstance(o["name"],str):invalid(r,"Invalid accessibility node"); continue
                l=o["locator"]
                if not isinstance(l,dict) or set(l)!={"kind","value"} or l.get("kind") not in {"test_id","dom_id","accessibility_path"} or not isinstance(l.get("value"),str) or not norm(l["value"]) or (l["kind"],l["value"]) in locs:invalid(r,"Invalid or duplicate locator")
                else:locs.add((l["kind"],l["value"])); nodes[o["id"]]=o
            elif group=="artifacts":
                if set(o)!={"id","kind","path","sha256"} or o.get("kind")!="image" or not safe_path(o.get("path")) or not re.fullmatch(r"[0-9a-f]{64}",o.get("sha256","")):invalid(r,"Invalid artifact"); continue
                if hashlib.sha256(safe_path(o["path"]).read_bytes()).hexdigest()!=o["sha256"]:invalid(r,"Artifact hash mismatch")
                artifacts[o["id"]]=o
    pairs=set(); caps=[]
    for o in data["focus_expectations"]:
        if not isinstance(o,dict) or set(o)!={"control_ref","viewport_id"} or not ID.fullmatch(o.get("control_ref","")) or not ID.fullmatch(o.get("viewport_id","")) or o["control_ref"] not in nodes or nodes[o["control_ref"]]["role"] not in ROLES or (o["control_ref"],o["viewport_id"]) in pairs: invalid(r,"Invalid focus expectation")
        else:pairs.add((o["control_ref"],o["viewport_id"]))
    for o in data["captures"]:
        if not isinstance(o,dict) or set(o)!={"id","control_ref","state","input","viewport_id","artifact_id"} or o.get("control_ref") not in nodes or nodes[o["control_ref"]]["role"] not in ROLES or o.get("state")!="focus-visible" or o.get("input")!="keyboard" or not ID.fullmatch(o.get("viewport_id","")) or o.get("artifact_id") not in artifacts: invalid(r,"Invalid capture")
        else:caps.append(o)
    for code,cfg in data["checks"].items():
        if code not in CHECKS or not isinstance(cfg,dict) or set(cfg)-{"applicability","coverage","reason"} or cfg.get("applicability") not in {"applicable","not_applicable","unknown"} or cfg.get("coverage") not in {"complete","partial","none"} or (cfg["applicability"] in {"unknown","not_applicable"} and not substantive(cfg.get("reason",""))):invalid(r,"Invalid check declaration")
        else:r.coverage[code]={k:cfg[k] for k in ("applicability","coverage","reason") if k in cfg}
    if r.invalid:return
    for code,cfg in r.coverage.items():
        app,cov=cfg["applicability"],cfg["coverage"]
        if app=="not_applicable":r.check(code,CHECKS[code],"skipped");continue
        if app=="unknown" or cov!="complete":r.add("UX_EVIDENCE_INSUFFICIENT","info","evidence",str(ep.relative_to(root)) if ep.is_relative_to(root) else str(ep),code,f"{code}: {app}/{cov}",INSUFF);r.check(code,CHECKS[code],"insufficient");continue
        if code=="UX_RENDER_CONTROL_NAME_MISSING":
            eligible=[n for n in nodes.values() if n["role"] in ROLES]
            if not eligible:
                r.add("UX_EVIDENCE_INSUFFICIENT","info","evidence","",code,"No eligible normalized controls",INSUFF)
                r.check(code,"render","insufficient")
                continue
            for n in eligible:
                if n["role"] in ROLES and not norm(n["name"]):r.add(code,"error","render","",n["id"],str(n["locator"]),"Trusts producer normalization; not a complete accessibility audit and purpose is not inferred.",n["id"])
        elif code=="UX_RENDER_FOCUS_EVIDENCE_MISSING":
            eligible=[n for n in nodes.values() if n["role"] in ROLES]
            if not eligible or not pairs or any(n["id"] not in {ref for ref,_ in pairs} for n in eligible):
                r.add("UX_EVIDENCE_INSUFFICIENT","info","evidence","",code,"Eligible controls cannot be completely joined",INSUFF);r.check(code,"render","insufficient");continue
            for ref,vp in pairs:
                if not any(c["control_ref"]==ref and c["viewport_id"]==vp for c in caps):r.add(code,"error","render","",f"control_ref={ref};viewport_id={vp}",str(nodes[ref]["locator"]),"Missing verification evidence, not proof that focus styling is absent/invisible.",ref)
        else:
            insufficiency_count=sum(d["code"]=="UX_EVIDENCE_INSUFFICIENT" for d in r.diags)
            source_observations(root, data["sources"], code, r)
            if any(d["code"]==code and d["level"]=="error" for d in r.diags):
                r.check(code,CHECKS[code],"violation")
                continue
            if sum(d["code"]=="UX_EVIDENCE_INSUFFICIENT" for d in r.diags) > insufficiency_count:
                r.check(code,CHECKS[code],"insufficient")
                continue
        r.check(code,CHECKS[code],"violation" if any(d["code"]==code and d["level"]=="error" for d in r.diags) else "passed")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--evidence"); ap.add_argument("--format",choices=("text","json"),default="text"); a=ap.parse_args(); r=Result()
    try:
        root=Path(a.root).resolve()
        if not root.is_dir(): raise ValueError("--root is not a directory")
        document(root,r)
        if a.evidence: evidence(root,Path(a.evidence).resolve(),r)
    except Exception as e: invalid(r,"Invocation/internal error: "+str(e))
    r.diags.sort(key=lambda d:(d["code"],d["path"],d["location"],d.get("evidence_id", "")))
    status="invalid" if r.invalid else "violations" if any(d["level"]=="error" for d in r.diags) else "clean"
    out={"schema_version":1,"status":status,"checks_performed":sorted(r.performed,key=lambda x:(x["code"],x["domain"])),"evidence_coverage":r.coverage,"diagnostics":r.diags}
    if a.format=="json": print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    else:
        print("no listed violations detected in checks performed" if status=="clean" else status)
        for d in r.diags:print(f"{d['level']} {d['code']} {d['path']} {d['location']}: {d['observed']} [{d['limitation']}]")
    return 2 if r.invalid else 1 if status=="violations" else 0
if __name__=="__main__": sys.exit(main())
