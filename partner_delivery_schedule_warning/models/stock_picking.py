# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import format_datetime


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @property
    def STEP_NAMES(self):
        return {
            "Pick": self.env._("Pick"),
            "Pack": self.env._("Pack"),
            "Delivery": self.env._("Delivery"),
        }

    picking_steps = fields.Text(
        compute="_compute_picking_steps", store=False, readonly=True
    )
    partner_delivery_schedule_warning = fields.Text(
        string="Delivery Schedule Warning / Info",
        compute="_compute_partner_delivery_schedule_warning",
        store=False,
        readonly=True,
    )
    partner_pickings_schedule_info = fields.Text(
        string="Pickings Schedule Info",
        store=False,
        readonly=True,
    )

    @api.depends("scheduled_date", "move_ids.rule_id")
    def _compute_picking_steps(self):
        for picking in self:
            steps_info = picking._get_following_pickings_info()
            steps_list = []
            current_step_found = False
            current_step = picking.picking_type_id.name
            prev_step_name = None
            prev_step_date = fields.Datetime.from_string(picking.scheduled_date)

            for step_name, step_code, _step_dt, delay in steps_info:
                if (
                    current_step_found
                    or step_name == current_step
                    or step_code == "outgoing"
                ):
                    if not current_step_found:
                        display_dt = prev_step_date
                        delay_from = None
                        delay_days = None
                    else:
                        display_dt = prev_step_date + timedelta(days=delay)
                        delay_from = prev_step_name if delay > 0 else None
                        delay_days = delay if delay > 0 else None

                    step_name_translated = self.STEP_NAMES.get(step_name, step_name)
                    steps_list.append(
                        {
                            "step_name": step_name_translated,
                            "step_name_eng": step_name,
                            "scheduled_date": fields.Datetime.to_string(display_dt),
                            "delay_from": self.env._(delay_from)
                            if delay_from
                            else None,
                            "delay_from_eng": delay_from,
                            "delay_days": delay_days,
                        }
                    )

                    current_step_found = True
                    prev_step_name = step_name
                    prev_step_date = display_dt

            picking.picking_steps = json.dumps(steps_list)

    def get_steps_list(self):
        self.ensure_one()
        return json.loads(self.picking_steps) if self.picking_steps else []

    def _get_final_step_datetime(self):
        self.ensure_one()
        steps = self.get_steps_list()
        if not steps:
            return None
        return fields.Datetime.from_string(steps[-1]["scheduled_date"])

    def _get_following_pickings_info(self):
        self.ensure_one()
        infos = []

        if not self.scheduled_date or not self.picking_type_id:
            return infos

        warehouse = self.picking_type_id.warehouse_id
        if not warehouse:
            return infos

        route_type = (
            warehouse.reception_steps
            if self.picking_type_code == "incoming"
            else warehouse.delivery_steps
        )

        if route_type == "ship_only":
            steps = [("Delivery", "outgoing")]
        elif route_type == "pick_ship":
            steps = [("Pick", "internal"), ("Delivery", "outgoing")]
        elif route_type == "pick_pack_ship":
            steps = [
                ("Pick", "internal"),
                ("Pack", "internal"),
                ("Delivery", "outgoing"),
            ]
        else:
            steps = [(self.picking_type_id.name, self.picking_type_id.code)]

        move = self.move_ids[:1]
        route_rules = (
            move.rule_id.route_id.rule_ids
            if move and move.rule_id and move.rule_id.route_id
            else []
        )
        base_dt = fields.Datetime.from_string(self.scheduled_date)

        for step_name, step_code in steps:
            step_delay = 0.0
            for rule in route_rules:
                if rule.picking_type_id and (
                    rule.picking_type_id.name == step_name
                    or rule.picking_type_id.code == "outgoing"
                ):
                    step_delay = rule.delay or 0.0
                    break
            infos.append((step_name, step_code, base_dt, step_delay))
            base_dt += timedelta(days=step_delay)

        return infos

    @api.depends("picking_steps", "partner_id", "partner_id.delivery_schedule_ids")
    def _compute_partner_delivery_schedule_warning(self):
        for picking in self:
            picking.partner_delivery_schedule_warning = ""
            picking.partner_pickings_schedule_info = ""
            if not picking.partner_id or picking.state in ["done", "cancel"]:
                continue

            final_dt = picking._get_final_step_datetime()
            if not final_dt:
                picking.partner_delivery_schedule_warning = picking.env._(
                    "No final step datetime available."
                )
                continue

            if not picking.partner_id.delivery_schedule_ids:
                planned_info = picking._get_pickings_schedule_info()
                picking.partner_pickings_schedule_info = picking.env._(
                    "INFO: No delivery schedule defined for partner."
                    "\n\n%(planned_info)s",
                    planned_info=planned_info,
                )
                continue

            partner_dt = fields.Datetime.context_timestamp(picking.partner_id, final_dt)
            dt_str = fields.Datetime.to_string(partner_dt.replace(tzinfo=None))
            if not picking.partner_id.allow_delivery_date(dt_str):
                schedule_str = "\n".join(
                    f"- {s.name} {s.display_name}"
                    for s in picking.partner_id.delivery_schedule_ids
                ) or picking.env._("No delivery schedule defined")
                user_dt_str = format_datetime(
                    picking.with_context(lang=picking.env.user.lang).env,
                    final_dt,
                    dt_format="short",
                )
                planned_info = picking._get_pickings_schedule_info()
                picking.partner_delivery_schedule_warning = picking.env._(
                    "ALERT: The planned final delivery date %(date)s does NOT match "
                    "the partner schedule:\n%(schedule_str)s\n\n%(planned_info)s",
                    date=user_dt_str,
                    schedule_str=schedule_str,
                    planned_info=planned_info,
                )
            else:
                picking.partner_pickings_schedule_info = (
                    picking._get_pickings_schedule_info()
                )

    def _get_pickings_schedule_info(self):
        infos = []
        if self.picking_type_id.code == "outgoing":
            infos.append(self.env._("Planned date:"))
        else:
            infos.append(self.env._("Planned dates based on route delay(s):"))

        user_env = self.with_context(lang=self.env.user.lang).env

        for step in self.get_steps_list():
            dt_utc = fields.Datetime.from_string(step["scheduled_date"])
            dt_str = format_datetime(user_env, dt_utc, dt_format="short")
            step_name_translated = self.env._(step["step_name"])
            delay_info = ""
            if step.get("delay_from"):
                delay_info = self.env._(
                    "- Delay from %(prev_step)s: %(days)s day(s)",
                    prev_step=self.env._(step["delay_from_eng"]),
                    days=step["delay_days"],
                )

            step_info = "- {step}: {date}{delay}".format(
                step=step_name_translated,
                date=dt_str,
                delay=f" {delay_info}" if delay_info else "",
            )

            if (
                step.get("step_name_eng") == "Delivery"
                and self.partner_id
                and self.partner_id.delivery_schedule_ids
            ):
                final_dt = self._get_final_step_datetime()
                partner_dt = fields.Datetime.context_timestamp(
                    self.partner_id, final_dt
                )
                partner_dt_naive = partner_dt.replace(tzinfo=None)
                if self.partner_id.allow_delivery_date(partner_dt_naive):
                    for schedule in self.partner_id.delivery_schedule_ids:
                        step_info += self.env._(
                            " **%(schedule)s: %(display_name)s**",
                            schedule=self.env._(schedule.name),
                            display_name=schedule.display_name,
                        )
                        break

            infos.append(step_info)

        return "\n".join(infos)
