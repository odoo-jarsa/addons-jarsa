# -*- coding: utf-8 -*-
# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from zeep import Client
from openerp import _, api, fields, models, registry, SUPERUSER_ID
from openerp.exceptions import ValidationError
from openerp.http import request


class ResUsers(models.Model):
    _inherit = 'res.users'

    biokey = fields.Char(
        string='Biokey',
    )

    def enrollment(self, biokey):
        ngrok_url = self.pool.get('ir.config_parameter').get_param(
            'ngrok_url_parameter')
        client = Client(ngrok_url)
        token = client.service.GetToken()['outToken']
        transaction = client.service.GetTmpTransNum(token)['outTmpTransNum']
        client.service.CaptureFinger(
            inToken=token,
            inTmpTransNum=transaction,
            inFlat=True,
            inRoll=False,
            inThumbR=False,
            inIndexR=True,
            inMiddleR=False,
            inRingR=False,
            inLittleR=False,
            inThumbL=False,
            inIndexL=False,
            inMiddleL=False,
            inRingL=False,
            inLittleL=False,
        )
        client.service.SendToServer(token, transaction)
        biokey = client.service.ServerFind(transaction, biokey)['outBioKey']
        return client, token, transaction, biokey

    @api.multi
    def fingerprint(self):
        self.ensure_one()
        client, token, transaction, biokey = self.enrollment(biokey='')
        if biokey:
            appkey = client.service.GetAppKey(biokey, 'Odoo')['outAppKey']
            if appkey:
                res_user = self.browse(int(appkey))
                if self.id != res_user.id:
                    raise ValidationError(
                        _('This exits for user %s', res_user.name))
            else:
                client.service.ServerSave(transaction, 'Odoo', appkey)
        else:
            biokey = client.service.ServerSave(
                transaction, 'Odoo', self.id)['outBioKey']
            self.biokey = biokey

    def _login(self, db, login, password):
        user_id = super(ResUsers, self)._login(db, login, password)
        if not user_id:
            return user_id
        if user_id == SUPERUSER_ID:
            return user_id
        with registry(db).cursor() as cr:
            cr.execute("SELECT biokey FROM res_users WHERE id = %s" % (
                user_id,))
            user_biokey = cr.fetchone()
        if request.session.login:
            return user_id
        client, token, transaction, biokey = self.enrollment(
            biokey=user_biokey[0])
        if not biokey:
            user_id = False
        return user_id
