##############################################################################

{
    'name': "Project Additional Sales",

    'summary': """
         Project Additional Sales""",

    'description': """
        Project Additional Sales
    """,

    'author': "PPTS India Pvt Ltd",
    'website': "https://pptssolutions.com",
    'category': 'Base',
    'version': '0.1',
    'depends': ['ppts_project_entries','sale'],

    'data': [
        'security/ir.model.access.csv',
        'views/project_entries_view.xml',
        'views/sale_view.xml',
    ],
}
