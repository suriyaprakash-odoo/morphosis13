# -*- coding: utf-8 -*-
{
    'name': 'Internal Project',
    'category': 'Inventory',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Internal project for managing second process',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base', 'ppts_inventory_customization','ppts_project_entries'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/vrac_process_view.xml',
        'views/internal_project_view.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
