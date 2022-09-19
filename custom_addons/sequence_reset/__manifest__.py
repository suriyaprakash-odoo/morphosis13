# -*- coding: utf-8 -*-mail_template
{
    'name': 'Reset Sequences Weekly',
    'category': 'Purchase',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Reset Sequences Weekly',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','stock'],
    'data': [
        'data/cron_data.xml',
        'views/ir_sequence.xml',
        'views/stock_production_lot.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
