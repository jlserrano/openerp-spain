# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 NaN (http://www.nan-tic.com) All Rights Reserved.
#                       Albert Cervera i Areny <albert@nan-tic.com>
#    $Id$
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#    Pablo Rocandio <salbet@gmail.com>
#
# Rehecho de nuevo para instalación OpenERP 5.0.0 sobre account_payment_extension: Zikzakmedia S.L. 2009
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Adaptacion de la norma 34-01 para emision de pagos. Validado para La Caixa: 2012
#   Joan M. Grande <totaler@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from tools.translate import _
from converter import *

class csb_34_01:
    def _start_34(self, cr, context):
        return convert(cr, self.order.mode.bank_id.partner_id.vat[2:], 10, context, 'right')

    def _cabecera_ordenante_34(self, cr, uid, context):
        today = datetime.today().strftime('%d%m%y')

        text = ''

        # Primer tipo
        text += '0356'
        text += self._start_34(cr, context)
        text += '34016'
        text += 7*' '
        text += '001'
        text += today
        if self.order.date_planned:
            planned = datetime.strptime(self.order.date_planned, '%Y-%m-%d')
            text += planned.strftime('%d%m%y')
        else:
            text += today
        #text += self.convert(self.order.mode.nombre, 40)
        ccc = bank_account_parts(cr, self.order.mode.bank_id.acc_number, self.order.mode.partner_id.name, context)
        text += ccc['bank']
        text += ccc['office']
        text += ccc['account']
        text += '0' #Detalle de cargo
        text += '1' #Gastos por cuenta del ordenante
        text += 2*' '
        text += ccc['dc']
        text += 7*' '
        text += '\n'

        # Segundo Tipo 
        text += '0356'
        text += self._start_34(cr, context)
        text += '34016'
        text += 7*' '
        text += '002'
        text += convert(cr, self.order.mode.bank_id.partner_id.name, 36, context)
        text += 7*' '
        text += '\n'

        # Tercer Tipo 
        text += '0356'
        text += self._start_34(cr, context)
        text += '34016'
        text += 7*' '
        text += '003'
        # Direccion
        address_id = self.pool.get('res.partner').address_get(cr, uid, [self.order.mode.bank_id.partner_id.id], ['invoice'])['invoice']
        if not address_id:
            raise Log( _('User error:\n\nCompany %s has no invoicing address.') % address_id )

        street = self.pool.get('res.partner.address').read(cr, uid, [address_id], ['street'], context)[0]['street']
        text += convert(cr, street, 36, context)
        text += 7*' '
        text += '\n'

        # Cuarto Tipo 
        text += '0356'
        text += self._start_34(cr, context)
        text += '34016'
        text += 7*' '
        text += '004'
        city = self.pool.get('res.partner.address').read(cr, uid, [address_id], ['city'], context)[0]['city']
        text += convert(cr, city, 36, context)
        text += 7*' '
        text += '\n'
        return text

    def _detalle_nacionales_34(self, cr, uid, recibo, context):
        # Primer Registro
        text = ''
        text += '0656'
        text += self._start_34(cr, context)
        if not recibo['partner_id'].vat:
            raise Log( _('User error:\n\nCompany %s has no vat.') % recibo['partner_id'].name )    
        text += convert(cr, recibo['partner_id'].vat[2:], 12, context, 'right')
        text += '010'
        text += convert(cr, recibo['amount'], 12, context)
        #text += convert_bank_account(cr, recibo['bank_id'].acc_number, recibo['partner_id'].name, context)
        #ccc = recibo['bank_id'] and recibo['bank_id'].acc_number or ''
        ccc = bank_account_parts(cr, recibo['bank_id'].acc_number, recibo['partner_id'].name, context)
        text += ccc['bank']
        text += ccc['office']
        text += ccc['account']
        text += ' '
        text += '9' # Otros conceptos (ni Nomina ni Pension)
        text += 2*' '
        text += ccc['dc']
        text += 7*' '
        text += '\n'

        # Segundo Registro
        text += '0656'
        text += self._start_34(cr, context)
        if not recibo['partner_id'].vat:
            raise Log( _('User error:\n\nCompany %s has no vat.') % recibo['partner_id'].name ) 
        text += convert(cr, recibo['partner_id'].vat[2:], 12, context, 'right')
        text += '011'
        text += convert(cr, recibo['partner_id'].name, 36, context)
        text += 7*' '
        text += '\n'
        return text

    def _totales_nacionales_34(self, cr, uid, context):
        text = '0856'
        text += self._start_34(cr, context)
        text += 12*' '
        text += 3*' '
        text += convert(cr, self.order.total, 12, context)
        text += convert(cr, self.payment_line_count, 8, context)
        text += convert(cr, self.record_count, 10, context)
        text += 6*' '
        text += 7*' '
        text += '\n'
        return text

    def create_file(self, pool, cr, uid, order, lines, context):
        self.pool = pool
        self.order = order
        self.context = context

        self.payment_line_count = 0
        self.record_count = 0

        file = ''
        file += self._cabecera_ordenante_34(cr, uid, context)
        self.record_count += 4
        for recibo in lines:
            file += self._detalle_nacionales_34(cr, uid, recibo, context)
            self.payment_line_count += 1
            self.record_count += 2
        self.record_count += 1
        file += self._totales_nacionales_34(cr, uid, context)
        
        return file

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
