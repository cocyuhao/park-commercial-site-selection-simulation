from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = ROOT / "40_quality_evidence"
DEFAULT_DOCX = ROOT / "80_delivery" / "osen_integrated_site_selection_report_20260606.docx"
DEFAULT_OUT_DIR = QUALITY_DIR / "osen_report_docx_render_20260606"
SOFFICE = Path(r"C:\Program Files\LibreOffice\program\soffice.com")


def _file_uri(path: Path) -> str:
    return "file:///" + path.resolve().as_posix()


def _safe_clean_dir(path: Path) -> None:
    resolved = path.resolve()
    quality = QUALITY_DIR.resolve()
    if quality not in resolved.parents and resolved != quality:
        raise RuntimeError(f"refuse to clean outside quality dir: {resolved}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def convert_docx_to_pdf(docx_path: Path, output_dir: Path) -> tuple[Path, dict[str, str | int | None]]:
    if not SOFFICE.exists():
        raise FileNotFoundError(f"LibreOffice console launcher not found: {SOFFICE}")
    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX not found: {docx_path}")

    with tempfile.TemporaryDirectory(prefix="codex_lo_profile_") as profile_dir_raw:
        with tempfile.TemporaryDirectory(prefix="codex_docx_render_") as work_dir_raw:
            profile_dir = Path(profile_dir_raw)
            work_dir = Path(work_dir_raw)
            temp_docx = work_dir / "report.docx"
            shutil.copy2(docx_path, temp_docx)

            cmd = [
                str(SOFFICE),
                f"-env:UserInstallation={_file_uri(profile_dir)}",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(work_dir),
                str(temp_docx),
            ]
            run = subprocess.run(
                cmd,
                cwd=str(work_dir),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=180,
                check=False,
            )
            pdf_path = work_dir / "report.pdf"
            if run.returncode not in (0, None) or not pdf_path.exists() or pdf_path.stat().st_size < 1000:
                raise RuntimeError(
                    "LibreOffice conversion failed\n"
                    f"returncode={run.returncode}\nstdout={run.stdout}\nstderr={run.stderr}"
                )

            final_pdf = output_dir / "osen_integrated_site_selection_report_20260606.pdf"
            shutil.copy2(pdf_path, final_pdf)
            return final_pdf, {
                "returncode": run.returncode,
                "stdout": run.stdout.strip(),
                "stderr": run.stderr.strip(),
                "profile_mode": "isolated_temp_user_installation",
            }


def render_pdf_pages(pdf_path: Path, output_dir: Path, zoom: float) -> list[dict[str, object]]:
    doc = fitz.open(pdf_path)
    rendered: list[dict[str, object]] = []
    try:
        matrix = fitz.Matrix(zoom, zoom)
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            png_path = output_dir / f"page_{page_index + 1:02d}.png"
            pix.save(png_path)
            rendered.append(
                {
                    "page": page_index + 1,
                    "png": str(png_path),
                    "bytes": png_path.stat().st_size,
                    "width": pix.width,
                    "height": pix.height,
                }
            )
    finally:
        doc.close()
    return rendered


def build_report(docx_path: Path, output_dir: Path, zoom: float) -> dict[str, object]:
    _safe_clean_dir(output_dir)
    pdf_path, conversion = convert_docx_to_pdf(docx_path, output_dir)
    pages = render_pdf_pages(pdf_path, output_dir, zoom)
    failures: list[str] = []
    if not pages:
        failures.append("no rendered pages")
    if any(int(page["bytes"]) < 5000 for page in pages):
        failures.append("one or more rendered pages are unexpectedly small")

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if not failures else "fail",
        "docx": str(docx_path),
        "output_dir": str(output_dir),
        "pdf": str(pdf_path),
        "pdf_bytes": pdf_path.stat().st_size,
        "page_count": len(pages),
        "render_zoom": zoom,
        "conversion": conversion,
        "pages": pages,
        "failures": failures,
        "method": "LibreOffice soffice.com with isolated UserInstallation, then PyMuPDF page rasterization",
    }
    (QUALITY_DIR / "osen_report_docx_render_20260606.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    md_lines = [
        "# 奥森 DOCX 渲染验证（2026-06-06）",
        "",
        f"- 状态：{report['status']}",
        f"- DOCX：`{docx_path}`",
        f"- PDF：`{pdf_path}`",
        f"- 页数：{len(pages)}",
        f"- 方法：{report['method']}",
        f"- LibreOffice 输出：{conversion.get('stdout', '')}",
    ]
    if conversion.get("stderr"):
        md_lines.append(f"- LibreOffice stderr：`{conversion['stderr']}`")
    if failures:
        md_lines.extend(["", "## 失败项", *[f"- {item}" for item in failures]])
    else:
        md_lines.extend(["", "## 页面截图", *[f"- page {p['page']}: `{p['png']}` ({p['width']}x{p['height']})" for p in pages]])
    (QUALITY_DIR / "osen_report_docx_render_20260606.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--zoom", type=float, default=2.0)
    args = parser.parse_args()

    report = build_report(args.docx.resolve(), args.out_dir.resolve(), args.zoom)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
