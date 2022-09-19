# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Inter company Sales',
    'category': 'Sales',
    'sequence': 100,
    'summary': 'Morphosis Sales customization',
    'website': 'http://www.pptssolutions.com',
    'author': 'PPTS [India] Pvt.Ltd.',
    'version': '13.1',
    'description': """
        Sale orders for inter company.
        """,
    'depends': ['sale','stock','sales_team','ppts_inventory_customization','ppts_custom_sale','ppts_project_entries'],
    'data': [
        'views/sale_views.xml',
        'views/stock_picking_view.xml',
        'views/purchase_view.xml',

    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
