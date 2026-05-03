import markdown
import os

md_file = "TensorX_Project_Final_Document.md"
html_output = "TensorX_Project_Final_Document.html"

with open(md_file, "r", encoding="utf-8") as f:
    text = f.read()

html = markdown.markdown(text, extensions=['extra', 'tables'])

# Add some basic styling to make it look professional
styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', sans-serif; padding: 50px; line-height: 1.6; color: #333; }}
        h1 {{ color: #1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }}
        h2 {{ color: #1e3a8a; margin-top: 30px; }}
        h3 {{ color: #3b82f6; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f8fafc; }}
        img {{ max-width: 100%; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
{html}
</body>
</html>
"""

with open(html_output, "w", encoding="utf-8") as f:
    f.write(styled_html)

print(f"Created {html_output}")
