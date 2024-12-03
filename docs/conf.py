import datetime

project = 'CSP.py'
author = 'KP Labs'
copyright = f'{datetime.datetime.now().year}, {author}'

primary_domain = None
numfig = True
language = 'en'

extensions = [
    'sphinx_immaterial'
]
html_theme = 'sphinx_immaterial'
root_doc = 'index'

html_theme_options = {
    'features': [
        'toc.follow'
    ],
    'font':  {
        'text': 'Fira Sans',
        'code': 'Fira Code',
    }
}