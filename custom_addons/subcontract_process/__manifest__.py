# -*- coding: utf-8 -*-mail_template
{
    'name': 'Morphosis Sub contract Process',
    'category': 'Purchase',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Morphosis Sub contract Process',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','ppts_inventory_customization','stock','ppts_project_entries','sale','inter_company_sales','ppts_custom_sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/update_so_view.xml',
        'data/sequence.xml',
        'views/sub_contract_view.xml',
        'views/sale_order_view.xml',
        'views/purchase_order.xml',
        'views/stock_picking_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
