import base64
import os

files_to_encode = [
    "_- visual selection (1).png",
    "_- visual selection (2).png",
    "_- visual selection (3).png",
    "_- visual selection (4).png",
    "jsk_dashboard_preview.png"
]

html_files = ["HACKATHON_PPT.html", "HACKATHON_PPT_ULTRA.html"]

for html_file in html_files:
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    for file_name in files_to_encode:
        if os.path.exists(file_name):
            with open(file_name, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                data_uri = f"data:image/png;base64,{encoded_string}"
                html_content = html_content.replace(f"./{file_name}", data_uri)
                html_content = html_content.replace(file_name, data_uri)
    
    output_file = html_file.replace(".html", "_STANDALONE.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Created {output_file}")
