# -*- coding: utf-8 -*-
{
    'name': 'Project Documents',
    'category': 'document',
    'version': '13.0',
    'sequence': 10,
    'summary': 'To store the project documents',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','ppts_project_entries','ppts_inventory_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_docs_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
