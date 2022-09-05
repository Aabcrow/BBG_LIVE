# -*- coding: utf-8 -*-
{
    'name': 'E9 PRODUCTION - BASE MODULE',
    'version': '1.0.0',
    'category': 'Hidden',
    'author': 'Abderrahmane Guessoum - Alpha Brains Technologies',
    'website': 'www.fiverr.com/aabcrow',
    'depends': [
        'sale',
        'account',
        'sale_project_account',
    ],
    'data': [
        # 'data/data.xml',

        'report/invoice_report.xml',
        'report/invoice_inherit_report.xml',
        'report/sale_order_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
