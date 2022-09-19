# -*- coding: utf-8 -*-
{
    'name': 'Stock Volume Report',
    'category': 'report',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Stock volume report',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','ppts_inventory_customization'],
    'data': [
        'wizard/stock_volume_wizard.xml',
        'views/inventory_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
