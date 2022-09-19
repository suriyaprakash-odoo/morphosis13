##############################################################################

{
    'name': "Customer Base Configurations",

    'summary': """
         Customer Base Configurations.""",

    'description': """
        Customer Base Configurations.
    """,

    'author': "PPTS India Pvt Ltd",
    'website': "https://pptssolutions.com",
    'category': 'Base',
    'version': '0.1',
    'depends': ['base','account','account_accountant','ppts_project_entries'],

    'data': [
        'views/res_partner_view.xml',
        'views/account.xml',
        'views/report_invoice.xml',
    ],
}
