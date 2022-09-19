# -*- coding: utf-8 -*-
{
    'name': 'Web PDF Report Preview',
    'version': '1.0',
    'category': 'Website',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Allow you to preview the PDF report before downloading.',
    'description': """

Allow you to preview the PDF report before downloading.


""",
    'depends': ['base','web'],
    'data': [
        'views/web.xml',
    ],
    'qweb': [
        #'static/src/xml/web.xml'
    ],
    'images': [
        'static/description/a1.png',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 30,
    'currency': 'EUR',
}
