# -*- coding: utf-8 -*-
{
    'name': 'Custom Logistics',
    'category': 'Fleet',
    'version': '13.0',
    'sequence': 5,
    'summary': 'Custom logistics for transportation',
    "website": "http://www.pptssolutions.com",
    "author": "PPTS [India] Pvt.Ltd.",
    'description': """
    """,
    'depends': ['base','product','purchase','mail','sale','stock','contacts','ppts_project_entries','stock'],
    'data': [
        'security/logistics_security.xml',
        'security/ir.model.access.csv',
        'wizard/update_container_details_view.xml',
        'wizard/transport_rfq_wizard_view.xml',
        'wizard/search_chronopost_project_view.xml',
        'wizard/ecologic_report_view.xml',
        'views/logistics_views.xml',     
        'views/purchase_views.xml',
        'report/logistics_report.xml',   
        'report/bsd_report_template.xml',
        'report/annux7_report_template.xml',
        # 'report/transport_rfq_report_template.xml',
        'report/transport_rfq_report_template_new.xml',
        'report/transport_po_report.xml',
        'data/mail_template.xml',        
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
