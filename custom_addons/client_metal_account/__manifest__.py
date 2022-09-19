##############################################################################

{
    'name': "Client Metal Account Process",
    'summary': """Credit remaining precious metal to client's account""",
    'description': """Credit remaining precious metal to client's account""",
    'author': "PPTS India Pvt Ltd",
    'website': "https://pptssolutions.com",
    'category': 'Base',
    'version': '0.1',
    'depends': ['ppts_project_entries','stock','base','mrp','ppts_inventory_customization'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/client_metal_account_view.xml',
        'views/project_entree_view.xml',
        'views/product_views.xml',
        'views/res_partner_view.xml',
        'views/res_company.xml',
    ],
}
