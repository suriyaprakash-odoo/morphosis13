# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales/PO un-paid report',
    'category': 'Sales',
    'sequence': 100,
    'summary': 'Morphosis Sales customization',
    'website': 'http://www.pptssolutions.com',
    'author': 'PPTS [India] Pvt.Ltd.',
    'version': '13.1',
    'description': """
        Sales/PO un-billed report
        """,
    'depends': ['sale','purchase','account','ppts_inventory_customization'],
    'data': [
        'views/billing_report.xml',
    ],
    'installable': True,
    'application': True,
}
