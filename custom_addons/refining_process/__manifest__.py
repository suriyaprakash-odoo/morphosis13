# -*- coding: utf-8 -*-
{
    'name': 'Refining Process flow',
    'category': 'refining',
    'version': '13.0',
    'sequence': 10,
    'summary': 'Refining process flow of Morphosis',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['ppts_project_entries','ppts_inventory_customization','ppts_logistics','mrp','product','container_subcontracting','mrp_account_enterprise'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/create_mo.xml',
        'views/logistics_view.xml',
        'views/project_entree_view.xml',
        'views/container_view.xml',
        'views/mrp_production.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
