
html = open('ppt_template.html', encoding='utf-8').read()
with open('HACKATHON_PPT.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
