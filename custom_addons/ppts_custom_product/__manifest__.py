# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Morphosis Product customization',
    'category': 'Product',
    'sequence': 100,
    'summary': 'Morphosis Product customization',
    'website': 'http://www.pptssolutions.com',
    'author': 'PPTS [India] Pvt.Ltd.',
    'version': '13.1',
    'description': """
        Adding containers in product.
        """,
    'depends': ['crm','product','sale','sale_crm','purchase','ppts_inventory_customization'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',

    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
