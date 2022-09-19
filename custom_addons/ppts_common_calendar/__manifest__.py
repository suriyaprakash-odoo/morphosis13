# -*- coding: utf-8 -*-mail_template
{
    'name': 'Custom Calendar',
    'category': 'calender',
    'version': '13.0.1',
    'sequence': 5,
    'summary': 'Centralised calendar for logistics and production',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','calendar','ppts_project_entries','ppts_logistics','ppts_inventory_customization'],
    'data': [
        'views/calendar_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
