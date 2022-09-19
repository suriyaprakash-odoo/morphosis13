# -*- encoding: utf-8 -*-
{
    'name': 'PPTS Custom Barcodes',
    'version': '13.0',
    'author': 'PPTS [India] Pvt.Ltd.',
    'category': 'Barcodes',
    'description': """This module allows you to scan the barcode to create operations in project entries
    """,
    'summary':"Scans the barcodes and views it's related form.",
    'depends': [
                'base', 
                'stock_barcode', 
                'barcodes', 
                'barcodes_mobile', 
                'purchase', 
                'sale', 
                'product', 
                'stock', 
                'stock_barcode',
                'stock_barcode_mobile', 
                'web_mobile',
                'event_barcode_mobile',
                'ppts_inventory_customization'
                ],
    # 'qweb': ['static/xml/barcode_menu.xml'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_barcode_template.xml',
        'views/tree_view_wizard.xml',
        'views/cron.xml',
        ],
    'images': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
