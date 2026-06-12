#!/usr/bin/env python3
"""
finalize_prisma.py — wire PRISMA numbers into the worksheet and figure.

Two uses:

  (1) Just the arXiv identification count (Task 1):
        python3 finalize_prisma.py --arxiv 512

      Writes the count to Search Log!D7 of screening-worksheet.xlsx, then sets
      \\nArXiv and \\nIdentified (= 268+15+417+arXiv) in figures/prisma_flow.tex.

  (2) Full screening + included counts (Task 2), once you have screened records:
        python3 finalize_prisma.py --arxiv 512 \\
            --dup 140 --auto 0 --other 0 \\
            --exclscreen 380 --assessed 192 \\
            --ec 60 40 30 25 12 9 \\
            --snow 6 --included 22

      All screening-stage values come from YOUR record-by-record screening in
      the worksheet's Screening sheet / PRISMA Counts sheet — never invent them.

Then recompile the figure:
        cd figures && pdflatex prisma_flow.tex
"""
import argparse, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent                      # .../methodology
REPO = HERE.parent                                          # Awesome-LLM-Agent-Evaluation
WORKSHEET = HERE / "screening-worksheet.xlsx"
# figure lives in the submission tree; adjust if you keep a different copy
TEX_CANDIDATES = [
    REPO.parent / "AIR_submission" / "figures" / "prisma_flow.tex",
    REPO.parent / "prisma_flow.tex",
]

IEEE, ACM, SPRINGER = 268, 15, 417


def set_macro(text, name, value):
    pat = re.compile(r"(\\newcommand\{\\" + re.escape(name) + r"\}\{)[^}]*(\})")
    if not pat.search(text):
        raise SystemExit(f"macro \\{name} not found in figure")
    return pat.sub(lambda m: m.group(1) + str(value) + m.group(2), text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arxiv", type=int, required=True)
    ap.add_argument("--dup", type=int)
    ap.add_argument("--auto", type=int, default=0)
    ap.add_argument("--other", type=int, default=0)
    ap.add_argument("--exclscreen", type=int)
    ap.add_argument("--assessed", type=int)
    ap.add_argument("--ec", type=int, nargs=6, metavar=("EC1","EC2","EC3","EC4","EC5","EC6"))
    ap.add_argument("--snow", type=int)
    ap.add_argument("--included", type=int)
    a = ap.parse_args()

    identified = IEEE + ACM + SPRINGER + a.arxiv

    # 1) worksheet: write arXiv count into Search Log!D7
    try:
        import openpyxl
        wb = openpyxl.load_workbook(WORKSHEET)
        wb["Search Log"]["D7"] = a.arxiv
        wb.save(WORKSHEET)
        print(f"[worksheet] Search Log!D7 = {a.arxiv}  (total identified = {identified})")
    except Exception as e:
        print(f"[worksheet] WARNING: {e}", file=sys.stderr)

    # 2) figure macros
    tex_path = next((p for p in TEX_CANDIDATES if p.exists()), None)
    if not tex_path:
        raise SystemExit("prisma_flow.tex not found")
    t = tex_path.read_text()
    t = set_macro(t, "nArXiv", a.arxiv)
    t = set_macro(t, "nIdentified", identified)

    # optional screening-stage macros
    opt = {"nDup": a.dup, "nAuto": a.auto, "nOther": a.other,
           "nExclScreen": a.exclscreen, "nAssessed": a.assessed,
           "nSnow": a.snow, "nIncluded": a.included}
    for name, val in opt.items():
        if val is not None:
            t = set_macro(t, name, val)
    if a.ec:
        for name, val in zip(["ECa","ECb","ECc","ECd","ECe","ECf"], a.ec):
            t = set_macro(t, name, val)

    # arithmetic sanity check if a full set was supplied
    if a.assessed is not None and a.ec and a.included is not None:
        lhs, rhs = a.assessed, sum(a.ec) + a.included
        print(f"[check] assessed={lhs}  vs  EC1..6+included={rhs}  ->  "
              + ("OK" if lhs == rhs else "MISMATCH (fix before submitting)"))

    tex_path.write_text(t)
    print(f"[figure] updated {tex_path}")
    print(f"         \\nArXiv={a.arxiv}  \\nIdentified={identified}")
    print("Now: cd " + str(tex_path.parent) + " && pdflatex prisma_flow.tex")


if __name__ == "__main__":
    main()
