# -*- coding: utf-8 -*-
###########################################################################
#
#    @author Xpath Solutions <xpathsolution@gmail.com>
#
###########################################################################


{
    'name': 'Purchase Advance Payment',
    'version': '1.0',
    'author': 'Xpath Solutions',
    'category': 'Purchases',
    'license': 'OPL-1',
    'summary': """Make advance payment in Purchase
    purchases advance payment purchase advance payment advance purchases payment advance po payment
    """,
    'description': '''Advance payments in Purchase and then use in Invoices''',
    'depends': ['purchase', 'account'],
    'data': ['wizard/purchase_advance_payment_wizard_view.xml',
             'views/purchase_view.xml',
             'security/ir.model.access.csv',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
    'price': 19.99,
    'currency': 'EUR',
    'images': ['static/description/banner.jpg'],
}
