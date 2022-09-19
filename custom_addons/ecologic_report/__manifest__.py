# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Ecologic Report',
    'category': 'Sales',
    'sequence': 100,
    'summary': 'Morphosis Ecologic Report',
    'website': 'http://www.pptssolutions.com',
    'author': 'PPTS [India] Pvt.Ltd.',
    'version': '13.1',
    'description': """
        Ecologic Report.
        """,
    'depends': ['base','ppts_project_entries'],
    'data': [
        'views/ecologic_report_view.xml',

    ],
    'installable': True,
    'application': True,
}
