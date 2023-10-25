# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#################################################################################
# Author      : Teqstars (<https://www.teqstars.com/>)
# Copyright(c): 2016-Present Teqstars
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
    'name': 'Insufficient Stock Units Warning for Kit',
    'version': '11.0',
    'category': 'Sales',
    'author': 'Teqstars',
    'website': 'https://teqstars.com',
    'support': 'support@teqstars.com',
    'maintainer': 'Teqstars',
    'license': 'AGPL-3',
    'summary': "Insufficient stock warning while selecting consumable kit type product in sale order line. ",
    'depends': ['sale_management','mrp'],
    'data': [
    ],
    'qweb': [],
    'images': ['static/description/images/main_screen.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 0.0,
    'currency': 'EUR',
}