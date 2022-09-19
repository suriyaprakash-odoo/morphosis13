# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Morphosis CRM customization',
    'category': 'CRM',
    'sequence': 100,
    'summary': 'Morphosis CRM customization',
    'website': 'http://www.pptssolutions.com',
    'author': 'PPTS [India] Pvt.Ltd.',
    'version': '13.1',
    'description': """
        Adding time based banner to the website
        """,
    'depends': [
        'crm',
        'sale',
        'sale_crm',
        'purchase',
        'product',
        'ppts_inventory_customization',
        'ppts_custom_sale',
        'morphosis_settings',
        'ppts_project_entries'
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_custom_views.xml',
        'views/custom_purchase_view.xml',
        'views/custom_sale_view.xml',
        'data/mail_template.xml',
        # 'views/res_partner_view.xml'
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
