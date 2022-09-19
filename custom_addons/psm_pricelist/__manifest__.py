# -*- coding: utf-8 -*-mail_template
{
    'name': 'Morphosis PSM Price list',
    'category': 'Purchase',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Morphosis PSM Price list',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','purchase','ppts_inventory_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/psm_pricelist_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
