# -*- coding: utf-8 -*-
{
    'name': 'Sub contracting Process',
    'category': 'Project',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Sub contracting process to handle some containers',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base', 'ppts_inventory_customization'],
    'data': [
        'wizard/create_po.xml',
        'views/sub_contracting_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
