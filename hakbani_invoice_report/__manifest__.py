# -*-coding: utf-8 -*-
{
    "name": "Hakbani-IT Invoice Report",
    "summary": "Hakbani-IT Invoice Report",
    "version": "15.0.0.0",
    "category": "account",
    "author": "Hakbani IT",
    'website': 'https://www.nutechits.com',
    "license": "AGPL-3",
    "depends": ["account", "l10n_sa_invoice"],
    "data": [
        "reports/invoice_report.xml",
        "reports/records.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
