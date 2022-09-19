# -*- coding: utf-8 -*-
{
    'name': 'Laboratory Report',
    'category': 'report',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Laboratory Report for refining',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','ppts_project_entries','ppts_inventory_customization','refining_process'],
    'data': [
        'security/ir.model.access.csv',
        'views/mail_template.xml',
        'views/laboratory_report.xml',
        'views/project_entree_view.xml',
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
