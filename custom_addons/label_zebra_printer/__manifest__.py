# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<https://www.kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.kanakinfosystems.com/license>
#################################################################################

{
    'name': 'Label Printing From Zebra Printer',
    'version': '1.0',
    'summary': 'An app which helps to send labels directly to the zebra label printer',
    'description': """
This module provides to print product,location and shipping label from Zebra Printer
====================================================================================

    """,
    'category': 'Printer',
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'images': ['static/description/banner.jpg'],
    'depends': ['sale_stock', 'barcodes', 'ppts_inventory_customization'],
    'data': [
        'views/zebra_printer_view.xml',
        'views/res_company_view.xml',
    ],
    'sequence': 1,
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 50,
    'currency': 'EUR',
    'live_test_url': 'https://www.youtube.com/watch?v=O8OVx2GxuGM',
}
