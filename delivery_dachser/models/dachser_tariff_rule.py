# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import math

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .dachser_master_data import DACHSER_RATE_TYPES


class DachserTariffRule(models.Model):
    _name = "dachser.tariff.rule"
    _description = "Dachser Transport Tariff Rule by Zone / Weight / Pallet"
    _order = "sequence, min_weight, id"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Delivery Method",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(
        string="Zone / Rule Description",
        required=True,
    )
    country_ids = fields.Many2many(
        comodel_name="res.country",
        relation="dachser_tariff_rule_country_rel",
        column1="rule_id",
        column2="country_id",
        string="Countries",
        help="If left empty, applies to any country allowed by the carrier.",
    )
    state_ids = fields.Many2many(
        comodel_name="res.country.state",
        relation="dachser_tariff_rule_state_rel",
        column1="rule_id",
        column2="state_id",
        string="States / Provinces",
        help="If left empty, applies to any state/province in the country.",
    )
    zip_prefixes = fields.Char(
        string="ZIP / Postal Code Prefixes",
        help=(
            "Comma-separated postal code prefixes (e.g. '07, 35, 38'). "
            "Leave empty for all."
        ),
    )
    min_weight = fields.Float(
        string="Min. Weight (kg)",
        default=0.0,
        help="Minimum chargeable weight (inclusive) in kilograms.",
    )
    max_weight = fields.Float(
        string="Max. Weight (kg)",
        default=0.0,
        help="Maximum chargeable weight (inclusive) in kilograms. 0 = No upper limit.",
    )
    min_pallets = fields.Integer(
        string="Min. Packages / Pallets",
        default=0,
        help="Minimum number of packages or pallets (0 = no minimum).",
    )
    max_pallets = fields.Integer(
        string="Max. Packages / Pallets",
        default=0,
        help="Maximum number of packages or pallets (0 = no limit).",
    )
    rate_type = fields.Selection(
        selection=DACHSER_RATE_TYPES,
        string="Calculation Mode",
        default="per_excess_kg",
        required=True,
    )
    base_price = fields.Float(
        string="Base Price (€)",
        digits="Product Price",
        default=0.0,
    )
    included_weight = fields.Float(
        string="Included Kg in Base",
        default=0.0,
        help="In 'Excess Kg' mode, kilograms already included in the base price.",
    )
    price_per_kg = fields.Float(
        string="Price / Kg or Fraction (€)",
        digits=(12, 4),
        default=0.0,
        help=(
            "Price per kg (or per 100 kg fraction when calculation mode is "
            "'100 Kg Fraction')."
        ),
    )
    price_per_pallet = fields.Float(
        string="Price / Pallet or Package (€)",
        digits="Product Price",
        default=0.0,
    )
    min_charge = fields.Float(
        string="Minimum Charge (€)",
        digits="Product Price",
        default=0.0,
        help="Minimum guaranteed freight charge before surcharges.",
    )
    fuel_surcharge_pct = fields.Float(
        string="Fuel Surcharge (%)",
        default=0.0,
        help=(
            "If 0, uses the default fuel surcharge percentage configured "
            "on the delivery method."
        ),
    )
    tail_lift_surcharge = fields.Float(
        string="Tail-Lift Surcharge (€)",
        digits="Product Price",
        default=0.0,
        help=(
            "If 0, uses the default tail-lift surcharge configured "
            "on the delivery method."
        ),
    )
    notice_surcharge = fields.Float(
        string="Delivery Notice Surcharge (€)",
        digits="Product Price",
        default=0.0,
        help=(
            "If 0, uses the default delivery notice surcharge configured "
            "on the delivery method."
        ),
    )
    currency_id = fields.Many2one(
        related="carrier_id.currency_id",
        string="Currency",
        readonly=True,
    )

    @api.constrains("min_weight", "max_weight", "min_pallets", "max_pallets")
    def _check_weight_and_pallet_ranges(self):
        for rule in self:
            if rule.max_weight > 0.0 and rule.min_weight > rule.max_weight:
                raise ValidationError(
                    _(
                        "In rule '%s', Minimum Weight cannot be greater than "
                        "Maximum Weight."
                    )
                    % rule.name
                )
            if rule.max_pallets > 0 and rule.min_pallets > rule.max_pallets:
                raise ValidationError(
                    _(
                        "In rule '%s', Minimum Pallets/Packages cannot be "
                        "greater than Maximum."
                    )
                    % rule.name
                )

    def _match_destination_and_shipment(
        self, partner, chargeable_weight_kg, packages_qty=1
    ):
        """Return True if this rule applies to the consignee partner,
        chargeable weight, and package count.
        """
        self.ensure_one()
        if self.country_ids and partner.country_id not in self.country_ids:
            return False
        if self.state_ids and partner.state_id not in self.state_ids:
            return False
        if self.zip_prefixes:
            partner_zip = (partner.zip or "").strip().upper()
            prefixes = [
                p.strip().upper() for p in self.zip_prefixes.split(",") if p.strip()
            ]
            if prefixes and (
                not partner_zip
                or not any(partner_zip.startswith(pref) for pref in prefixes)
            ):
                return False
        if self.min_weight and chargeable_weight_kg < self.min_weight:
            return False
        if self.max_weight > 0.0 and chargeable_weight_kg > self.max_weight:
            return False
        if self.min_pallets and packages_qty < self.min_pallets:
            return False
        if self.max_pallets > 0 and packages_qty > self.max_pallets:
            return False
        return True

    def _compute_rule_cost(
        self,
        chargeable_weight_kg,
        packages_qty=1,
        tail_lift=False,
        has_notice=False,
    ):
        """Compute total cost and breakdown text for this tariff rule."""
        self.ensure_one()
        carrier = self.carrier_id
        eff_packages = max(1, int(packages_qty or 1))
        weight = max(0.0, float(chargeable_weight_kg or 0.0))

        if self.rate_type == "fixed":
            freight = self.base_price
        elif self.rate_type == "per_kg":
            freight = self.base_price + (weight * self.price_per_kg)
        elif self.rate_type == "per_excess_kg":
            threshold = (
                self.included_weight
                if self.included_weight > 0.0
                else (self.min_weight or 0.0)
            )
            excess_kg = max(0.0, weight - threshold)
            freight = self.base_price + (excess_kg * self.price_per_kg)
        elif self.rate_type == "per_100kg":
            fractions = math.ceil(max(0.01, weight) / 100.0)
            freight = self.base_price + (fractions * self.price_per_kg)
        elif self.rate_type == "per_pallet":
            freight = self.base_price + (eff_packages * self.price_per_pallet)
        else:
            freight = self.base_price

        if self.min_charge and freight < self.min_charge:
            freight = self.min_charge

        lines = [
            _("• Applied rule: %(rule)s — Base freight: %(freight).2f €")
            % {"rule": self.name, "freight": freight}
        ]
        total = freight

        fuel_pct = (
            self.fuel_surcharge_pct
            if self.fuel_surcharge_pct > 0.0
            else (carrier.dachser_fuel_surcharge_pct or 0.0)
        )
        if fuel_pct > 0.0:
            fuel_amt = freight * (fuel_pct / 100.0)
            total += fuel_amt
            lines.append(
                _("• Fuel surcharge (%(pct).2f%%): %(amt).2f €")
                % {"pct": fuel_pct, "amt": fuel_amt}
            )

        if tail_lift:
            tl_amt = (
                self.tail_lift_surcharge
                if self.tail_lift_surcharge > 0.0
                else (carrier.dachser_tail_lift_surcharge or 0.0)
            )
            if tl_amt > 0.0:
                total += tl_amt
                lines.append(_("• Tail-lift surcharge: %.2f €") % tl_amt)

        if has_notice:
            notice_amt = (
                self.notice_surcharge
                if self.notice_surcharge > 0.0
                else (carrier.dachser_notice_surcharge or 0.0)
            )
            if notice_amt > 0.0:
                total += notice_amt
                lines.append(_("• Delivery notice surcharge: %.2f €") % notice_amt)

        lines.append(_("Total Local Dachser Tariff: %.2f €") % total)
        return round(total, 2), "\n".join(lines)
