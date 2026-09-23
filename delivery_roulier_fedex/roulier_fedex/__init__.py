#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)

try:
    from . import carrier_action
except ImportError:
    _logger.debug("Cannot `import roulier`.")
