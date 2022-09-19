# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Morphosis Sales customization',
    'category': 'Sales',
    'sequence': 100,
    'summary': 'Morphosis Sales customization',
    'website': 'http://www.pptssolutions.com',
    'author': 'PPTS [India] Pvt.Ltd.',
    'version': '13.1',
    'description': """
        Adding containers in sale order line based on the product selected.
        """,
    'depends': ['crm','product','sale','sale_crm','purchase','ppts_inventory_customization','ppts_custom_product','ppts_project_entries','ppts_logistics','sales_team'],
    'data': [
        # 'security/ir.model.access.csv',
        'wizard/sales_picking_list_views.xml',
        'wizard/transport_popup_view.xml',
        'report/quotation_report_inherited.xml',
        'views/process_type_view.xml',
        'views/sale_views.xml',
        'data/mail_template.xml',

    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
}
