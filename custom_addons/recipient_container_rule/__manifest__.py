# -*- coding: utf-8 -*-
{
    'name': 'Recipient container rule',
    'category': 'Inventory',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Recipient container record rule for Morphosis',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base', 'stock', 'ppts_project_entries', 'ppts_inventory_customization'],
    'data': [
        'security/security_groups.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
