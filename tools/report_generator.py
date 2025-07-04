import os
import pypandoc
import logging
import tempfile
import shutil

# إعداد Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_report(markdown_content, output_file="report.pdf"):
    try:
        # التحقق من توفر pandoc
        version = pypandoc.get_pandoc_version()
        logger.info(f"[✔] Pandoc version {version} detected.")

        # التحقق من توفر pdflatex
        if not shutil.which("pdflatex"):
            logger.error("[!] pdflatex not found. Please install TeX Live or a similar LaTeX distribution.")
            return "[!] pdflatex not found. Please install TeX Live."

        # إنشاء قالب LaTeX يدعم العربية
        latex_template = r"""
        \documentclass[a4paper,11pt]{article}
        \usepackage{booktabs}
        \usepackage{longtable}
        \usepackage[margin=0.8in]{geometry}
        \usepackage{parskip}
        \usepackage{array}
        \usepackage{polyglossia}
        \setmainlanguage{english}
        \setotherlanguage{arabic}
        \newfontfamily\arabicfont[Scale=1.2]{Amiri}
        \setlength{\parindent}{0pt}
        \newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
        \begin{document}
        \sffamily
        %s
        \end{document}
        """

        # تحويل الـ Markdown إلى ملف مؤقت
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as temp_md_file:
            temp_md_file.write(markdown_content)
            temp_md_path = temp_md_file.name
            logger.info(f"Temporary Markdown file created at: {temp_md_path}")

        # تحويل الـ Markdown إلى PDF
        pypandoc.convert_file(
            temp_md_path,
            "pdf",
            outputfile=output_file,
            extra_args=[
                "--pdf-engine=pdflatex",
                "--variable=geometry:margin=0.8in",
                "--variable=fontsize:11pt",
                "--variable=linestretch:1.1",
                "--variable=tables",
                "--variable=booktabs"
            ]
        )

        # حذف الملف المؤقت
        os.unlink(temp_md_path)
        logger.info(f"Temporary Markdown file deleted: {temp_md_path}")

        # التحقق من وجود ملف PDF
        if not os.path.exists(output_file):
            logger.error(f"[!] PDF file not found at {output_file} after generation.")
            return f"[!] PDF file not found at {output_file}."

        logger.info(f"✅ PDF created at {output_file}")
        return f"✅ PDF created at {output_file}"

    except Exception as e:
        logger.error(f"❌ PDF generation failed: {str(e)}", exc_info=True)
        return f"❌ PDF generation failed: {str(e)}"