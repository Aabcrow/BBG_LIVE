# -*- coding: utf-8 -*-
{
    'name': "Hakbani-IT Item Cart Report",
    'summary': """
    Witholding Report
    """,
    "author": "Hakbani IT",
    'website': 'https://www.nutechits.com',
    'category': 'stock',
    'version': '15.0.0.0',
    'depends': ['base', 'report_xlsx', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'wizard/inventory_valuation.xml',
    ],
}