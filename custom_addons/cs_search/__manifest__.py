# -*- coding: utf-8 -*-
{
    'name': 'CS Search',
    'category': 'Project',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Container Search',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base', 'ppts_inventory_customization', 'ppts_project_entries','internal_project'],
    'data': [
        'wizard/search_cs_wizard.xml',
        'views/search_cs_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
