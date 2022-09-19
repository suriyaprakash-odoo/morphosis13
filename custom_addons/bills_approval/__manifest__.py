##############################################################################

{
    'name': "Vendor Bills approval process",
    'summary': """Vendor Bills approval process""",
    'description': """Vendor Bills approval process""",
    'author': "PPTS India Pvt Ltd",
    'website': "https://pptssolutions.com",
    'category': 'Base',
    'version': '0.1',
    'depends': ['account','ppts_project_entries'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/account_invoice_view.xml',
        'views/res_company_view.xml'
    ],
}
