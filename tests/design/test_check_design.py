"""Acceptance coverage for the optional offline DESIGN.md checker; uses only temporary roots."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "design" / "scripts" / "check-design.py"
TEMPLATE = Path(__file__).resolve().parents[2] / "skills" / "design" / "templates" / "DESIGN.md"
MIGRATION_FIXTURES = Path(__file__).parent / "fixtures" / "migration-cases.json"
HEADINGS = ["Product Intent", "Principles", "Tokens", "Typography", "Layout and Responsive", "Primitives", "Interaction and Feedback", "Motion", "Accessibility", "Verification", "Accepted Debt"]


def design(data_bearing=False, motion=False):
    states = ["default", "hover", "active", "focus", "disabled", "loading"]
    if data_bearing:
        states += ["empty", "error"]
    primitive = "### Button\n\n- data_bearing: %s\n\n| state | specification | same_as | non_color_cue |\n|---|---|---|---|\n%s" % (str(data_bearing).lower(), "\n".join("| %s | detail | - | not_applicable |" % state for state in states))
    content = {heading: "- substantive declaration" for heading in HEADINGS}
    content["Primitives"] = primitive
    content["Motion"] = "- motion_present: %s\n- reduced_motion: %s" % (str(motion).lower(), "use no animation" if motion else "not_applicable")
    content["Accepted Debt"] = "| id | decision | date | upgrade_path |\n|---|---|---|---|\n| debt | known constraint | 2026-08-29 | upgrade by 2027-01-01 |"
    return "# Design System\n\n" + "\n\n".join("## %s\n\n%s" % (heading, content[heading]) for heading in HEADINGS) + "\n"


class CheckDesignAcceptanceTests(unittest.TestCase):
    """Focused acceptance scenarios; CLI calls cover output and exit semantics."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="design checker ")
        self.root = Path(self.temp.name) / "root with spaces"
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def put_design(self, content=None):
        target = self.root / "DESIGN.md"
        target.write_text(content or design(), encoding="utf-8")
        return target

    def invoke(self, evidence=None, fmt="json"):
        command = [sys.executable, str(SCRIPT), "--root", str(self.root), "--format", fmt]
        if evidence is not None:
            command += ["--evidence", str(evidence)]
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def manifest(self, **overrides):
        value = {"schema_version": 1, "producer": {"name": "unittest", "version": "1"}, "checks": {}, "sources": [], "accessibility_nodes": [], "focus_expectations": [], "captures": [], "artifacts": []}
        value.update(overrides)
        return value

    def evidence(self, data):
        target = self.root / "evidence.json"
        target.write_text(json.dumps(data), encoding="utf-8")
        return target

    def codes(self, response):
        return [item["code"] for item in json.loads(response.stdout)["diagnostics"]]

    def test_01_valid_minimal_exit_zero(self):
        self.put_design()
        response = self.invoke()
        self.assertEqual(response.returncode, 0)
        self.assertEqual(json.loads(response.stdout)["status"], "clean")

    def test_02_valid_data_bearing_comprehensive_exit_zero(self):
        self.put_design(design(data_bearing=True, motion=True))
        self.assertEqual(self.invoke().returncode, 0)

    def test_03_missing_legacy_and_dual_paths(self):
        missing = self.invoke(); self.assertEqual(missing.returncode, 1); self.assertIn("DESIGN_PATH_MISSING", self.codes(missing))
        (self.root / "docs").mkdir(); (self.root / "docs/design.md").write_text("legacy", encoding="utf-8")
        legacy = self.invoke(); self.assertIn("DESIGN_PATH_LEGACY", self.codes(legacy))
        self.put_design(); dual = self.invoke(); self.assertIn("DESIGN_PATH_CONFLICT", self.codes(dual))

    def test_04_heading_missing_order_duplicate_and_empty(self):
        text = design().replace("## Tokens\n\n- substantive declaration\n\n", "")
        text = text.replace("## Typography", "## TEMPORARY", 1).replace("## Accessibility", "## Typography", 1).replace("## TEMPORARY", "## Accessibility", 1)
        text += "\n## Principles\n\n"
        self.put_design(text)
        found = set(self.codes(self.invoke()))
        self.assertTrue({"DESIGN_SECTION_MISSING", "DESIGN_SECTION_ORDER", "DESIGN_SECTION_DUPLICATE", "DESIGN_SECTION_EMPTY"} <= found)

    def test_05_missing_data_bearing_and_required_states(self):
        text = design().replace("- data_bearing: false\n\n", "").replace("| loading | detail | - | not_applicable |\n", "")
        self.put_design(text)
        found = set(self.codes(self.invoke()))
        self.assertIn("DESIGN_FIELD_INVALID", found)
        # A data-bearing primitive independently requires empty/error.
        self.put_design(design(data_bearing=True).replace("| empty | detail | - | not_applicable |\n", "").replace("| error | detail | - | not_applicable |\n", ""))
        self.assertIn("DESIGN_STATE_MISSING", self.codes(self.invoke()))

    def test_06_same_as_valid_and_invalid(self):
        self.put_design(design().replace("| hover | detail | - | not_applicable |", "| hover | - | default | not_applicable |"))
        self.assertEqual(self.invoke().returncode, 0)
        self.put_design(design().replace("| hover | detail | - | not_applicable |", "| hover | detail | hover | not_applicable |"))
        self.assertIn("DESIGN_STATE_REFERENCE_INVALID", self.codes(self.invoke()))

    def test_07_non_color_cue_exact_and_near_misses(self):
        self.put_design(design().replace("| focus | detail | - | not_applicable |", "| focus | detail | - | none |"))
        self.assertIn("UX_DOC_NON_COLOR_CUE_NONE", self.codes(self.invoke()))
        prose = design().replace("- substantive declaration", "- Never use color only; quoted `none`; example: non_color_cue: none", 1)
        self.put_design(prose)
        self.assertNotIn("UX_DOC_NON_COLOR_CUE_NONE", self.codes(self.invoke()))

    def test_08_reduced_motion_and_debt_validation(self):
        self.put_design(design(motion=True)); self.assertEqual(self.invoke().returncode, 0)
        broken = design(motion=True).replace("reduced_motion: use no animation", "reduced_motion: none").replace("2026-08-29", "2026-02-30").replace("upgrade by 2027-01-01", "TODO")
        self.put_design(broken)
        found = set(self.codes(self.invoke()))
        self.assertTrue({"UX_DOC_REDUCED_MOTION_MISSING", "DESIGN_DEBT_DATE_MISSING", "DESIGN_DEBT_UPGRADE_MISSING"} <= found)

    def test_09_unicode_crlf_and_no_write_hash(self):
        target = self.put_design(design().replace("Button", "Bütton").replace("\n", "\r\n"))
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        self.assertEqual(self.invoke().returncode, 0)
        self.assertEqual(before, hashlib.sha256(target.read_bytes()).hexdigest())

    def test_10_text_json_fact_parity_and_exits(self):
        self.put_design(design().replace("| focus | detail | - | not_applicable |", "| focus | detail | - | none |"))
        structured = self.invoke(fmt="json"); text = self.invoke(fmt="text")
        self.assertEqual(structured.returncode, text.returncode)
        self.assertIn("UX_DOC_NON_COLOR_CUE_NONE", structured.stdout); self.assertIn("UX_DOC_NON_COLOR_CUE_NONE", text.stdout)
        self.assertEqual(self.invoke(self.evidence({"schema_version": 2})).returncode, 2)

    def test_11_malformed_version_unknown_key_and_duplicate_ids(self):
        self.put_design()
        for bad in ({"schema_version": 2}, self.manifest(unexpected=True), self.manifest(accessibility_nodes=[{"id":"same","role":"button","name":"A","locator":{"kind":"dom_id","value":"a"}}, {"id":"same","role":"button","name":"B","locator":{"kind":"test_id","value":"b"}}])):
            self.assertEqual(self.invoke(self.evidence(bad)).returncode, 2)

    def test_12_traversal_absolute_and_symlink_escape(self):
        self.put_design()
        for path in ("../escape.html", str(Path(self.temp.name) / "outside.html")):
            data = self.manifest(sources=[{"id":"src","kind":"html","path":path}])
            self.assertEqual(self.invoke(self.evidence(data)).returncode, 2)
        outside = Path(self.temp.name) / "outside.html"; outside.write_text("<button></button>")
        (self.root / "linked.html").symlink_to(outside)
        data = self.manifest(sources=[{"id":"src","kind":"html","path":"linked.html"}])
        self.assertEqual(self.invoke(self.evidence(data)).returncode, 2)

    def test_13_html_icon_literal_named_and_ambiguity(self):
        self.put_design(); html = self.root / "page.html"
        check = {"UX_SRC_ICON_CONTROL_NAME_MISSING":{"applicability":"applicable","coverage":"complete"}}
        html.write_text("<button><svg/></button>", encoding="utf-8")
        positive = self.invoke(self.evidence(self.manifest(checks=check, sources=[{"id":"html","kind":"html","path":"page.html"}]))); self.assertEqual(positive.returncode, 1); self.assertIn("UX_SRC_ICON_CONTROL_NAME_MISSING", self.codes(positive))
        html.write_text("<button aria-label='Save'><svg/></button>", encoding="utf-8")
        self.assertEqual(self.invoke(self.evidence(self.manifest(checks=check, sources=[{"id":"html","kind":"html","path":"page.html"}]))).returncode, 0)
        html.write_text("<button aria-labelledby='name'><svg/></button>", encoding="utf-8")
        ambiguous = self.invoke(self.evidence(self.manifest(checks=check, sources=[{"id":"html","kind":"html","path":"page.html"}]))); self.assertEqual(ambiguous.returncode, 0); self.assertIn("UX_EVIDENCE_INSUFFICIENT", self.codes(ambiguous))

    def test_14_css_motion_positive_qualifying_and_ambiguity(self):
        self.put_design(); css = self.root / "site.css"; check = {"UX_SRC_REDUCED_MOTION_MISSING":{"applicability":"applicable","coverage":"complete"}}
        def observe(value):
            css.write_text(value, encoding="utf-8")
            return self.invoke(self.evidence(self.manifest(checks=check, sources=[{"id":"css","kind":"css","path":"site.css"}])))
        self.assertIn("UX_SRC_REDUCED_MOTION_MISSING", self.codes(observe("a { animation-duration: 1s; }")))
        self.assertEqual(observe("a { animation-duration: 1s; } @media (prefers-reduced-motion: reduce) { a { animation-duration: 0s; } }").returncode, 0)
        for ambiguous in ("a { animation: spin 1s; }", "@import 'x.css'; a { animation-duration: 1s; }", "a { animation-duration: var(--speed); }"):
            response = observe(ambiguous); self.assertEqual(response.returncode, 0); self.assertIn("UX_EVIDENCE_INSUFFICIENT", self.codes(response))

    def node(self, ident="ax-save", role="button", kind="test_id", value="save", name="Save"):
        return {"id":ident,"role":role,"name":name,"locator":{"kind":kind,"value":value}}

    def test_15_control_ref_exact_join_and_missing_capture(self):
        self.put_design(); artifact = self.root / "focus.png"; artifact.write_bytes(b"focus")
        node = self.node(); checks = {"UX_RENDER_FOCUS_EVIDENCE_MISSING":{"applicability":"applicable","coverage":"complete"}}
        artifact_record = {"id":"shot","kind":"image","path":"focus.png","sha256":hashlib.sha256(b"focus").hexdigest()}
        good = self.manifest(checks=checks, accessibility_nodes=[node], focus_expectations=[{"control_ref":"ax-save","viewport_id":"desktop"}], captures=[{"id":"cap","control_ref":"ax-save","state":"focus-visible","input":"keyboard","viewport_id":"desktop","artifact_id":"shot"}], artifacts=[artifact_record])
        self.assertEqual(self.invoke(self.evidence(good)).returncode, 0)
        good["captures"] = []
        missing = self.invoke(self.evidence(good)); self.assertEqual(missing.returncode, 1); self.assertIn("UX_RENDER_FOCUS_EVIDENCE_MISSING", self.codes(missing))

    def test_16_locators_paths_unknown_and_ineligible_refs(self):
        self.put_design(); nodes = [self.node("one", value="save", kind="dom_id"), self.node("two", value="save", kind="test_id")]
        valid = self.manifest(accessibility_nodes=nodes)
        self.assertEqual(self.invoke(self.evidence(valid)).returncode, 0)
        path_node = self.node(kind="accessibility_path", value="dialog / Save [1]")
        self.assertEqual(self.invoke(self.evidence(self.manifest(accessibility_nodes=[path_node]))).returncode, 0)
        for node, ref in ((self.node(role="article"), "ax-save"), (self.node(), "missing")):
            bad = self.manifest(accessibility_nodes=[node], focus_expectations=[{"control_ref":ref,"viewport_id":"desktop"}])
            self.assertEqual(self.invoke(self.evidence(bad)).returncode, 2)

    def test_17_artifact_hash_mismatch_is_invalid(self):
        self.put_design(); artifact = self.root / "focus.png"; artifact.write_bytes(b"actual")
        data = self.manifest(artifacts=[{"id":"shot","kind":"image","path":"focus.png","sha256":"0" * 64}])
        self.assertEqual(self.invoke(self.evidence(data)).returncode, 2)

    def test_18_partial_and_unknown_coverage_are_info_exit_zero(self):
        self.put_design()
        for declaration in ({"applicability":"applicable","coverage":"partial"}, {"applicability":"unknown","coverage":"none","reason":"adapter omitted nodes"}):
            data = self.manifest(checks={"UX_RENDER_CONTROL_NAME_MISSING": declaration})
            response = self.invoke(self.evidence(data))
            payload = json.loads(response.stdout)
            self.assertEqual(response.returncode, 0)
            self.assertEqual(payload["status"], "clean")
            self.assertIn("UX_EVIDENCE_INSUFFICIENT", self.codes(response))
            self.assertEqual(
                [check["status"] for check in payload["checks_performed"] if check["domain"] == "render"],
                ["insufficient"],
            )
            self.assertFalse(any(diagnostic["level"] == "error" for diagnostic in payload["diagnostics"]))

    def test_19_document_boundaries_placeholders_cycles_and_debt(self):
        broken = design().replace("## Motion", "## Unknown\n\n- value\n\n## Motion").replace("- motion_present: false", "  - motion_present: false").replace("| hover | detail | - | not_applicable |", "| hover | - | active | not_applicable |").replace("| active | detail | - | not_applicable |", "| active | - | hover | not_applicable |").replace("| debt | known constraint | 2026-08-29 | upgrade by 2027-01-01 |", "| debt |  | 2026-08-29 | upgrade |\\n| debt | known | 2026-08-30 | upgrade |")
        self.put_design(broken); found=set(self.codes(self.invoke()))
        self.assertIn("DESIGN_FIELD_INVALID",found); self.assertIn("DESIGN_STATE_REFERENCE_INVALID",found)
        three=design().replace("| hover | detail | - | not_applicable |","| hover | - | active | not_applicable |").replace("| active | detail | - | not_applicable |","| active | - | focus | not_applicable |").replace("| focus | detail | - | not_applicable |","| focus | - | hover | not_applicable |")
        self.put_design(three); self.assertIn("DESIGN_STATE_REFERENCE_INVALID",self.codes(self.invoke()))
        self.put_design(design().replace("- substantive declaration","- TODO",1)); self.assertIn("DESIGN_SECTION_EMPTY",self.codes(self.invoke()))
        self.put_design(design().replace("- substantive declaration","### Heading only",1)); self.assertIn("DESIGN_SECTION_EMPTY",self.codes(self.invoke()))
        self.put_design(design().replace("- substantive declaration","| name | value |\\n|---|---|",1)); self.assertIn("DESIGN_SECTION_EMPTY",self.codes(self.invoke()))
        self.put_design(design().replace("## Tokens","\t## Tokens")); self.assertIn("DESIGN_SECTION_MISSING",self.codes(self.invoke()))
        self.put_design(design().replace("## Tokens","##\tTokens")); self.assertIn("DESIGN_SECTION_MISSING",self.codes(self.invoke()))
        self.put_design(design().replace("- motion_present: false","- motion_present: false\\n- extra_field: value")); self.assertIn("DESIGN_FIELD_INVALID",self.codes(self.invoke()))
        self.put_design(design().replace("- data_bearing: false","- data_bearing: false\\n- extra_field: value")); self.assertIn("DESIGN_FIELD_INVALID",self.codes(self.invoke()))

    def test_20_motion_false_mismatch_and_html_decision_table(self):
        self.put_design(design().replace("reduced_motion: not_applicable","reduced_motion: reduce"))
        self.assertIn("DESIGN_FIELD_INVALID",self.codes(self.invoke()))
        self.put_design()
        page=self.root/"page.html"; check={"UX_SRC_ICON_CONTROL_NAME_MISSING":{"applicability":"applicable","coverage":"complete"}}
        def observe(markup):
            page.write_text(markup,encoding="utf-8")
            return self.invoke(self.evidence(self.manifest(checks=check,sources=[{"id":"html","kind":"html","path":"page.html"}])))
        self.assertEqual(observe("<span id='a'>Save</span><span id='b'>now</span><button aria-labelledby='a b'><svg/></button>").returncode,0)
        for markup in ("<button aria-labelledby='missing'><svg/></button>","<button id='a' aria-labelledby='a'><svg/></button>","<span id='a' aria-labelledby='b'>A</span><span id='b' aria-labelledby='a'>B</span><button aria-labelledby='a'><svg/></button>","<i id='a'></i><i id='a'></i><button aria-labelledby='a'><svg/></button>","<button><custom-icon>Save</custom-icon></button>","<button><svg></button>"):
            response=observe(markup); self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        for markup in ("<button hidden><svg/></button>","<button><img alt='Save'></button>","<button><svg><title>Save</title></svg></button>"):
            self.assertEqual(observe(markup).returncode,0)
        for markup in ("<button><script>name</script><svg/></button>","<button><template>name</template><svg/></button>"):
            self.assertEqual(observe(markup).returncode,1)

    def test_21_css_scanner_boundaries(self):
        self.put_design(); css=self.root/"site.css"; check={"UX_SRC_REDUCED_MOTION_MISSING":{"applicability":"applicable","coverage":"complete"}}
        def observe(value):
            css.write_text(value,encoding="utf-8")
            return self.invoke(self.evidence(self.manifest(checks=check,sources=[{"id":"css","kind":"css","path":"site.css"}])))
        self.assertEqual(observe("/* animation-duration:1s */ a{transition-duration:0s}").returncode,0)
        self.assertEqual(observe("a::before{content:'animation-duration:1s'}a{transition-duration:0s}").returncode,0)
        self.assertIn("UX_SRC_REDUCED_MOTION_MISSING",self.codes(observe("a{animation-duration:0s,200ms}")))
        self.assertIn("UX_SRC_REDUCED_MOTION_MISSING",self.codes(observe("a{animation:spin 1s;animation-duration:1s}")))
        for value in ("a{animation:spin 1s}","a{animation-duration:var(--x)}","a{transition-duration:calc(1s)}","a{--speed:1s;animation-duration:var(--speed)}","@import 'x';a{animation-duration:1s}","a{animation-duration:1s","@media not (prefers-reduced-motion: reduce){a{animation-duration:0s}}a{animation-duration:1s}","@media (prefers-reduced-motion: no-preference){a{animation-duration:0s}}a{animation-duration:1s}","@media (prefers-reduced-motion: reduced){a{animation-duration:0s}}a{animation-duration:1s}"):
            response=observe(value); self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        self.assertEqual(observe("@media (prefers-reduced-motion: reduce){}a{animation-duration:1s}").returncode,1)
        self.assertEqual(observe("@media (prefers-reduced-motion: reduce){a{opacity:.5}}a{animation-duration:1s}").returncode,0)

    def test_22_render_empty_expectations_run_id_and_artifact_kind(self):
        self.put_design(); checks={"UX_RENDER_CONTROL_NAME_MISSING":{"applicability":"applicable","coverage":"complete"}}
        response=self.invoke(self.evidence(self.manifest(checks=checks))); self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        self.assertEqual([row["status"] for row in json.loads(response.stdout)["checks_performed"] if row["domain"]=="render"],["insufficient"])
        focus={"UX_RENDER_FOCUS_EVIDENCE_MISSING":{"applicability":"applicable","coverage":"complete"}}
        response=self.invoke(self.evidence(self.manifest(checks=focus,accessibility_nodes=[self.node()]))); self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        nodes=[self.node("one",value="one"),self.node("two",value="two")]
        response=self.invoke(self.evidence(self.manifest(checks=focus,accessibility_nodes=nodes,focus_expectations=[{"control_ref":"one","viewport_id":"desktop"}])))
        self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        bad=self.manifest(); bad["producer"]["run_id"]=""; self.assertEqual(self.invoke(self.evidence(bad)).returncode,2)
        bad=self.manifest(); bad["producer"]["name"]="   "; self.assertEqual(self.invoke(self.evidence(bad)).returncode,2)
        self.assertEqual(self.invoke(self.evidence(self.manifest(accessibility_nodes=[self.node(value="   ") ]))).returncode,2)
        image=self.root/"image.png"; image.write_bytes(b"x")
        bad=self.manifest(artifacts=[{"id":"shot","kind":"video","path":"image.png","sha256":hashlib.sha256(b"x").hexdigest()}]); self.assertEqual(self.invoke(self.evidence(bad)).returncode,2)

    def test_23_html_candidate_scoping_href_alt_and_title(self):
        self.put_design(); page=self.root/"page.html"; check={"UX_SRC_ICON_CONTROL_NAME_MISSING":{"applicability":"applicable","coverage":"complete"}}
        def observe(markup):
            page.write_text(markup,encoding="utf-8")
            return self.invoke(self.evidence(self.manifest(checks=check,sources=[{"id":"html","kind":"html","path":"page.html"}])))
        self.assertIn("UX_SRC_ICON_CONTROL_NAME_MISSING",self.codes(observe("<div>{{ unrelated }}</div><button><svg/></button>")))
        for markup in ("<button aria-label={label}><svg/></button>","<a href={target}><svg/></a>","<button id='same'><svg/></button><i id='same'></i>"):
            response=observe(markup); self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        self.assertIn("UX_SRC_ICON_CONTROL_NAME_MISSING",self.codes(observe("<button><img></button>")))
        non_svg_title=observe("<button><title>Save</title><svg/></button>")
        self.assertEqual(non_svg_title.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(non_svg_title))
        self.assertEqual(observe("<a href='   '><svg/></a>").returncode,0)
        mixed=observe("<button><svg/></button><button aria-label={label}><svg/></button>")
        mixed_payload=json.loads(mixed.stdout)
        self.assertEqual(mixed.returncode,1)
        self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(mixed))
        self.assertEqual([row["status"] for row in mixed_payload["checks_performed"] if row["domain"]=="source"],["violation"])

    def test_24_css_exact_properties_and_media_negation(self):
        self.put_design(); css=self.root/"site.css"; check={"UX_SRC_REDUCED_MOTION_MISSING":{"applicability":"applicable","coverage":"complete"}}
        def observe(value):
            css.write_text(value,encoding="utf-8")
            return self.invoke(self.evidence(self.manifest(checks=check,sources=[{"id":"css","kind":"css","path":"site.css"}])))
        for value in ("a{--animation-duration:1s}","a{-webkit-animation-duration:1s}","@media not screen and (prefers-reduced-motion: reduce){a{opacity:.5}}a{animation-duration:1s}","@media (prefers-reduced-motion: reduce) and (prefers-reduced-motion: reduce){a{opacity:.5}}a{animation-duration:1s}"):
            response=observe(value); self.assertEqual(response.returncode,0); self.assertIn("UX_EVIDENCE_INSUFFICIENT",self.codes(response))
        self.assertEqual(observe("@media screen and (prefers-reduced-motion: reduce){a{opacity:.5}}a{animation-duration:1s}").returncode,0)
        self.assertEqual(observe("@important x;a{animation-duration:1s}").returncode,1)

    def test_25_explicit_root_never_inherits_ancestor_design(self):
        self.put_design()
        app=self.root/"apps"/"store"; app.mkdir(parents=True)
        command=[sys.executable,str(SCRIPT),"--root",str(app),"--format","json"]
        missing=subprocess.run(command,text=True,capture_output=True,check=False)
        self.assertEqual(missing.returncode,1); self.assertIn("DESIGN_PATH_MISSING",self.codes(missing))
        (app/"DESIGN.md").write_text(design(data_bearing=True),encoding="utf-8")
        self.assertEqual(subprocess.run(command,text=True,capture_output=True,check=False).returncode,0)
        sibling=self.root/"apps"/"admin"; sibling.mkdir()
        (sibling/"DESIGN.md").write_text(design(motion=True),encoding="utf-8")
        sibling_command=[sys.executable,str(SCRIPT),"--root",str(sibling),"--format","json"]
        self.assertEqual(subprocess.run(sibling_command,text=True,capture_output=True,check=False).returncode,0)

    def test_26_unfilled_canonical_template_is_not_a_false_clean(self):
        self.put_design(TEMPLATE.read_text(encoding="utf-8"))
        response=self.invoke()
        self.assertEqual(response.returncode,1)
        self.assertIn("DESIGN_SECTION_EMPTY",self.codes(response))
        self.assertIn("DESIGN_FIELD_INVALID",self.codes(response))
        self.assertTrue(any(row["code"]=="DESIGN_SECTION_EMPTY" and row["observed"]=="Tokens" for row in json.loads(response.stdout)["diagnostics"]))

    def test_27_checker_explicit_root_scope_matrix(self):
        def run(root):
            return subprocess.run([sys.executable,str(SCRIPT),"--root",str(root),"--format","json"],text=True,capture_output=True,check=False)
        unified=self.root/"unified"; unified.mkdir(); (unified/"DESIGN.md").write_text(design(),encoding="utf-8")
        for name,legacy in (("same",design()),("contradictory","# incompatible legacy")):
            app=unified/"apps"/name; (app/"docs").mkdir(parents=True); (app/"docs"/"design.md").write_text(legacy,encoding="utf-8")
        self.assertEqual(run(unified).returncode,0)
        divergent=self.root/"divergent"
        for name in ("a","b"):
            legacy=divergent/name/"docs"; legacy.mkdir(parents=True); (legacy/"design.md").write_text("legacy",encoding="utf-8")
            response=run(divergent/name); self.assertEqual(response.returncode,1); self.assertIn("DESIGN_PATH_LEGACY",self.codes(response))
        (divergent/"a"/"DESIGN.md").write_text(design(),encoding="utf-8")
        self.assertEqual(run(divergent/"a").returncode,1)
        (divergent/"a"/"docs"/"design.md").unlink()
        self.assertEqual(run(divergent/"a").returncode,0)
        self.assertIn("DESIGN_PATH_LEGACY",self.codes(run(divergent/"b")))
        (divergent/"DESIGN.md").write_text(design(),encoding="utf-8")
        self.assertEqual(run(divergent/"a").returncode,0)
        (divergent/"a"/"docs").mkdir(exist_ok=True); (divergent/"a"/"docs"/"design.md").write_text("legacy",encoding="utf-8")
        (divergent/"b"/"DESIGN.md").write_text(design(),encoding="utf-8")
        self.assertIn("DESIGN_PATH_CONFLICT",self.codes(run(divergent/"a")))
        self.assertEqual(run(divergent/"b").returncode,1)
        (divergent/"b"/"docs"/"design.md").unlink()
        self.assertEqual(run(divergent/"b").returncode,0)
        early=self.root/"early"; (early/"docs").mkdir(parents=True); (early/"docs"/"design.md").write_text("legacy",encoding="utf-8")
        (early/"docs"/"design.md").unlink()
        self.assertIn("DESIGN_PATH_MISSING",self.codes(run(early)))
        (early/"DESIGN.md").write_text(design(),encoding="utf-8")
        self.assertEqual(run(early).returncode,0)

    def test_28_migration_decision_fixture_matrix(self):
        payload=json.loads(MIGRATION_FIXTURES.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"],1)
        self.assertEqual(len(payload["cases"]),9)
        for case in payload["cases"]:
            reason=None
            if case["classification"]=="unified" and case["legacy_relation"]=="contradictory":
                reason="contradictory-unification"
            elif case["classification"]=="divergent" and case["parent_artifact"] and not case["parent_deployable"]:
                reason="nondeployable-parent-conflict"
            elif case["dual_roots"]:
                reason="dual-root-conflict"
            elif case["delete_requested"] and not all(case["gates"].values()):
                reason="deletion-gate-incomplete"
            blocked=reason is not None
            self.assertEqual(blocked,case["expected"]["blocked"],case["id"])
            if blocked:
                self.assertEqual(reason,case["expected"]["reason"],case["id"])
            else:
                if case["classification"] in {"single","unified"}:
                    canonical="repository-root"
                elif case["id"]=="nested-deployable":
                    canonical="explicit-nested-root"
                else:
                    canonical="per-app"
                self.assertEqual(canonical,case["expected"]["canonical"],case["id"])
            apps=case.get("apps",{})
            complete=not blocked and all(case["gates"].values()) and (
                case["delete_requested"] or (bool(apps) and all(value=="root" for value in apps.values()))
            )
            self.assertEqual(complete,case["expected"]["repo_migration_complete"],case["id"])


if __name__ == "__main__":
    unittest.main()
