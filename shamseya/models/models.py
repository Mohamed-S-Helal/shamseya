# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


def get_years():
    year_list = []
    for i in range(2016, 2036):
        year_list.append((i, str(i)))
    return year_list


class ResUser(models.Model):
    _inherit = 'res.users'

    prefix = fields.Char()


class Area(models.Model):
    _name = 'area'

    name = fields.Char(required=1)
    country_id = fields.Many2one('res.country', default=lambda self: self.env.user.country_id)
    state_id = fields.Many2one('res.country.state', domain="[('country_id', '=?', country_id)]")


class Referral(models.Model):
    _name = 'referral'

    name = fields.Char(required=1)


class IncomeResource(models.Model):
    _name = 'income.resource'

    name = fields.Char(required=1)


class PensionType(models.Model):
    _name = 'pension.type'

    name = fields.Char(required=1)


class InsuranceType(models.Model):
    _name = 'insurance.type'

    name = fields.Char(required=1)


class Diagnosis(models.Model):
    _name = 'diagnosis'

    name = fields.Char(required=1)


class MedicalHistoryLine(models.Model):
    _name = 'medical.history.line'

    case_id = fields.Many2one('res.partner', store=1)
    diagnosis = fields.Many2one('diagnosis', required=1)
    start_date = fields.Date()
    duration_y = fields.Integer()
    duration_m = fields.Integer()
    duration = fields.Char(compute='_calculate_duration')
    medicine = fields.Many2one('medicine')

    @api.depends("start_date")
    def _calculate_duration(self):
        for rec in self:
            if rec.start_date:
                date_format = '%Y-%m-%d'
                current_date = (datetime.today()).strftime(date_format)
                d1 = rec.start_date
                d2 = datetime.strptime(current_date, date_format).date()
                r = relativedelta(d2, d1)
                rec.duration_y = r.years
                rec.duration_m = r.months
                rec.duration = f"{r.years} years, {r.months} months"
            else:
                rec.duration = ""


class Medicine(models.Model):
    _name = 'medicine'

    name = fields.Char()
    price = fields.Float()


class BasicService(models.Model):
    _name = 'basic.service'

    name = fields.Char(required=1)
    medicine = fields.Boolean()
    monthly = fields.Boolean()
    description = fields.Text()


class RequestState(models.Model):
    _name = 'request.state'

    name = fields.Char()
    description = fields.Text()
    monthly = fields.Boolean()


class MonthlyFollowUp(models.Model):
    _name = 'monthly.follow.up'

    request_id = fields.Many2one('case.request')
    date = fields.Date()
    status = fields.Selection([('in_process', 'In Process'), ('done', 'Done'), ('problem', 'Problem') ],
                             string='status', default='in_process')
    # month = fields.Selection([(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    #                           (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    #                           (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'), ],
    #                          string='Month', )
    # year = fields.Selection(get_years(), string='Year', default=datetime.now().year)
    # medicine = fields.Many2one('medicine')